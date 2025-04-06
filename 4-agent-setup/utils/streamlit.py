import streamlit as st
import uuid
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from utils.logger import logger
from utils.conversation import save_conversation, get_saved_conversations, load_conversation_messages
from utils.messaging import process_message_for_agent, create_initial_messages

def initialize_session_state(initializer):
    """Initialize Streamlit session state with necessary components."""
    # Generate a new session ID if not already set
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logger.info(f"🆕 Created new session: {st.session_state.session_id[:8]}...")

    # Initialize LLM if not already done
    if "llm" not in st.session_state:
        st.session_state.llm = initializer["llm"]()

    # Initialize embedding model and stores
    if "embedding_model" not in st.session_state:
        st.session_state.embedding_model = initializer["embedding_model"]()

    if "conversation_store" not in st.session_state:
        st.session_state.conversation_store = initializer["conversation_store"]["initialize"](
            st.session_state.embedding_model,
            initializer["conversation_store"]["persist_directory"],
            initializer["conversation_store"]["collection_name"]
        )

    if "knowledge_store" not in st.session_state:
        st.session_state.knowledge_store = initializer["knowledge_store"]["initialize"](
            st.session_state.embedding_model,
            initializer["knowledge_store"]["persist_directory"],
            initializer["knowledge_store"]["collection_name"]
        )

    # Initialize messages array if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = create_initial_messages(initializer["system_prompt"], initializer["welcome_message"])

    # Initialize conversation chain last, after all dependencies are set up
    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = initializer["agent"](
            st.session_state.llm,
            st.session_state.conversation_store,
            st.session_state.session_id,
            initializer["system_prompt"]
        )

def render_chat():
    """Render the chat messages in the Streamlit app"""
    logger.info(f"Rendering {len(st.session_state.messages)} messages")

    for i, message in enumerate(st.session_state.messages):
        try:
            if isinstance(message, HumanMessage):
                st.chat_message("user").markdown(message.content)
                logger.info(f"Rendered user message #{i}: {message.content[:30]}...")
            elif isinstance(message, AIMessage):
                logger.info(f"Rendering AI message #{i}: {message.content[:50]}...")
                # Handle both string and dict content
                if isinstance(message.content, dict):
                    st.chat_message("assistant").markdown(str(message.content))
                else:
                    st.chat_message("assistant").markdown(message.content)
            elif isinstance(message, SystemMessage):
                logger.info(f"Skipping system message #{i}")
                pass
            else:
                logger.warning(f"Unknown message type: {type(message)}")
        except Exception as e:
            logger.error(f"Error rendering message #{i}: {e}")
            # Continue rendering other messages even if one fails
            continue

def handle_user_input(prompt):
    """Process user input and generate a response"""
    logger.info(f"🗣️ User input: {prompt[:30]}...")

    # Add the user message to the history
    message = HumanMessage(content=prompt)
    st.session_state.messages.append(message)

    # Display the message in the UI
    st.chat_message("user").markdown(message.content)

    # Generate a response using the agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                logger.info("🤔 Generating response with tools...")

                # Process messages for the agent
                agent_messages = process_message_for_agent(st.session_state.messages)

                # Invoke the agent
                try:
                    response = st.session_state.conversation_chain.invoke(
                        {"messages": agent_messages}
                    )

                    logger.info(f"Agent response: {str(response)[:100]}...")

                    if response and "output" in response:
                        output_content = response["output"]
                        st.markdown(output_content)
                        st.session_state.messages.append(AIMessage(content=output_content))
                        logger.info("✅ Response generated successfully")
                    else:
                        error_msg = "Received empty or invalid response from agent"
                        logger.warning(error_msg)
                        fallback_response = "I'm sorry, I couldn't generate a proper response with my tools. Please try asking about a specific city for travel recommendations."
                        st.markdown(fallback_response)
                        st.session_state.messages.append(AIMessage(content=fallback_response))
                except Exception as agent_error:
                    logger.error(f"Agent error: {str(agent_error)}")
                    # Fallback to regular LLM if agent fails
                    filtered_messages = [m for m in st.session_state.messages if not isinstance(m, SystemMessage)][-5:]
                    fallback_response = st.session_state.llm.invoke(filtered_messages).content
                    st.markdown(fallback_response)
                    st.session_state.messages.append(AIMessage(content=fallback_response))
                    logger.info("✅ Fallback response generated")

            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                logger.error(error_msg)
                st.markdown(f"⚠️ {error_msg}")
                st.session_state.messages.append(AIMessage(content=f"I'm sorry, I encountered an error while processing your request. Please try again with a different question."))
                logger.exception("Exception details:")

def setup_sidebar(initializer):
    """Setup the sidebar with conversation controls"""
    st.sidebar.title("Chat Controls")

    # Create a new conversation button
    if st.sidebar.button("➕ New Conversation"):
        logger.info("🆕 Starting new conversation")
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = create_initial_messages(initializer["system_prompt"], initializer["welcome_message"])
        st.session_state.conversation_chain = initializer["agent"](
            st.session_state.llm,
            st.session_state.conversation_store,
            st.session_state.session_id,
            initializer["system_prompt"]
        )
        st.sidebar.success("New conversation started!")
        st.rerun()

    # Create a save conversation button
    if st.sidebar.button("💾 Save Conversation"):
        # Only save if we have more than just the system message and welcome message
        if len(st.session_state.messages) > 2:
            logger.info("💾 Saving current conversation")
            save_conversation(
                st.session_state.conversation_store,
                st.session_state.llm,
                st.session_state.messages,
                st.session_state.session_id
            )
            st.sidebar.success("Conversation saved successfully!")
        else:
            st.sidebar.warning("Start a conversation before saving")

    # Create a clear conversation button
    if st.sidebar.button("🗑️ Clear Conversation"):
        logger.info("🗑️ Clearing current conversation")
        st.session_state.messages = create_initial_messages(initializer["system_prompt"], initializer["welcome_message"])
        st.sidebar.success("Conversation cleared!")
        st.rerun()

    # Display saved conversations
    st.sidebar.divider()
    st.sidebar.subheader("Saved Conversations")

    saved_conversations = get_saved_conversations(st.session_state.conversation_store)
    if saved_conversations:
        for i, conv in enumerate(saved_conversations[:10]):  # Show only the 10 most recent
            # Use index to ensure unique keys
            conv_button_label = f"🗣️ {conv['title']} ({conv['message_count']} msgs)"
            unique_key = f"conv_{conv['id']}_{i}"
            if st.sidebar.button(conv_button_label, key=unique_key):
                logger.info(f"📂 Loading conversation: {conv['id'][:8]}...")
                loaded_messages = load_conversation_messages(
                    st.session_state.conversation_store,
                    conv['id'],
                    initializer["system_prompt"],
                    initializer["welcome_message"]
                )

                if loaded_messages:
                    st.session_state.session_id = conv['id']
                    st.session_state.messages = loaded_messages
                    st.sidebar.success(f"Loaded conversation: {conv['title']}")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to load conversation")
    else:
        st.sidebar.info("No saved conversations yet")
