import uuid
import datetime
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from utils.logger import logger
from utils.vector import save_document_to_store, get_documents_from_store

def create_context_summary(messages, llm):
    """Create a summary of the conversation to use as context for future interactions"""
    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful assistant that summarizes conversations. You help our travel assistant remember the conversation history.
        Your summary should include:
        1. Which cities the user has mentioned
        2. Any specific interests the user has expressed
        3. Travel plans or timeframes mentioned
        4. Any specific questions that were asked about those cities

        Here is the conversation history:
        {messages}

        Please provide a concise summary of the key points.
        """
    )
    chain = prompt | llm | StrOutputParser()
    summary = chain.invoke({"messages": messages})
    return summary

def save_conversation(conversation_store, llm, messages, session_id=None):
    """Save the current conversation to the vector store"""
    logger.info("💾 Saving conversation")

    if not session_id:
        session_id = str(uuid.uuid4())

    # Skip saving if there are no real messages (just system and welcome)
    user_msgs = sum(1 for m in messages if isinstance(m, HumanMessage))
    if user_msgs == 0:
        logger.info("⏭️ No user messages to save, skipping")
        return session_id

    # Check if this conversation already exists
    try:
        results = get_documents_from_store(conversation_store, {"session_id": session_id})

        # If this conversation exists and has the same message count, don't save again
        if results and results.get('metadatas') and len(results['metadatas']) > 0:
            existing_count = results['metadatas'][0].get("message_count", 0)
            current_count = len(messages)

            if existing_count == current_count:
                logger.info(f"✅ Conversation already saved (messages: {existing_count})")
                return session_id

            # Delete the old version before saving the new one
            logger.info(f"🔄 Updating conversation from {existing_count} to {current_count} messages")
            conversation_store.delete(
                where={"session_id": session_id}
            )
    except Exception as e:
        logger.warning(f"Error checking for existing conversation: {e}")

    # Convert message objects to strings for the context summary
    message_texts = []

    for m in messages:
        if isinstance(m, HumanMessage):
            message_texts.append(f"User: {m.content}")
        elif isinstance(m, AIMessage) and not isinstance(m.content, dict) and m.content.strip():
            # Save AI messages with a special marker at the start to preserve markdown
            # This ensures we properly delimit messages even if they contain newlines
            ai_content = m.content.strip()
            message_texts.append(f"Assistant: {ai_content}")
            # Log the size of content being saved
            logger.info(f"Saving AI message of length {len(ai_content)} characters")

    messages_str = "\n\n".join(message_texts)  # Double newline to better separate messages

    # Skip saving if there are no messages to save
    if not message_texts:
        logger.warning("No valid messages to save, skipping")
        return session_id

    # Generate a summary of the conversation for context
    context_summary = create_context_summary(messages_str, llm)

    # Create a document with the conversation content
    content_text = " ".join([m.content[:100] for m in messages if not isinstance(m, SystemMessage) and not isinstance(m.content, dict)])

    # Create metadata with all necessary information
    metadata = {
        "session_id": session_id,
        "messages": messages_str,
        "context_summary": context_summary,
        "timestamp": datetime.datetime.now().isoformat(),
        "message_count": len(messages),
        "user_message_count": user_msgs,
    }

    # Add to vector store
    save_document_to_store(conversation_store, content_text, metadata)

    logger.info(f"✅ Conversation saved successfully (ID: {session_id[:8]}...)")
    return session_id

def get_saved_conversations(conversation_store):
    """Get a list of saved conversations from the store"""
    try:
        # Get all documents from the store
        results = get_documents_from_store(conversation_store)

        if not results or not results.get('metadatas') or not results.get('ids'):
            return []

        conversations = []
        for i, metadata in enumerate(results['metadatas']):
            if metadata and "session_id" in metadata and "timestamp" in metadata:
                # Extract the first user message for the title, if available
                title = "Conversation"
                if "messages" in metadata:
                    messages = metadata["messages"].split("\n")
                    for msg in messages:
                        if msg.startswith("User: "):
                            # Use the first 30 chars as the title
                            title = msg[6:36] + ("..." if len(msg) > 36 else "")
                            break

                conversations.append({
                    "id": metadata["session_id"],
                    "title": title,
                    "timestamp": metadata["timestamp"],
                    "message_count": metadata.get("message_count", 0)
                })

        # Sort by timestamp, most recent first
        conversations.sort(key=lambda x: x["timestamp"], reverse=True)
        logger.info(f"📚 Found {len(conversations)} saved conversations")
        return conversations

    except Exception as e:
        logger.error(f"Error retrieving saved conversations: {e}")
        return []

def load_conversation(conversation_store, session_id):
    """Load a conversation from the store or return defaults if not found"""
    try:
        results = get_documents_from_store(conversation_store, {"session_id": session_id})

        if results and results.get('metadatas') and len(results['metadatas']) > 0:
            metadata = results['metadatas'][0]
            if "messages" in metadata and "context_summary" in metadata:
                logger.info(f"📂 Loaded conversation data for: {session_id[:8]}...")
                return {
                    "messages": metadata["messages"],
                    "context_summary": metadata["context_summary"]
                }

        # Return default values if conversation not found or doesn't have expected structure
        return {
            "messages": "",
            "context_summary": "This is a new conversation."
        }
    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        return {
            "messages": "",
            "context_summary": "Error loading previous conversation."
        }

def load_conversation_messages(conversation_store, session_id, system_prompt, welcome_message):
    """Load the messages for a specific conversation as message objects"""
    try:
        results = get_documents_from_store(conversation_store, {"session_id": session_id})

        if not results or not results.get('metadatas') or len(results['metadatas']) == 0:
            logger.warning(f"❓ No conversation found with ID: {session_id[:8]}...")
            return None

        metadata = results['metadatas'][0]
        if "messages" in metadata:
            messages_text = metadata["messages"]
            logger.info(f"Raw messages from store:\n{messages_text[:200]}..." if len(messages_text) > 200 else messages_text)

            # Convert text back to message objects
            parsed_messages = [SystemMessage(content=system_prompt)]

            # Split by line but preserve message boundaries
            lines = messages_text.split("\n")
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                if not line:
                    i += 1
                    continue

                if line.startswith("User: "):
                    # User messages are typically single line
                    content = line[6:]
                    parsed_messages.append(HumanMessage(content=content))
                    logger.info(f"Added user message: {content[:30]}...")
                    i += 1

                elif line.startswith("Assistant: "):
                    # AI messages can span multiple lines due to markdown
                    content = line[11:]  # Start with first line content
                    i += 1

                    # Continue collecting lines until we hit the next message marker
                    while i < len(lines) and not (lines[i].startswith("User: ") or lines[i].startswith("Assistant: ")):
                        content += "\n" + lines[i]
                        i += 1

                    # Only add if there's actual content
                    if content.strip():
                        parsed_messages.append(AIMessage(content=content))
                        logger.info(f"Added AI message: {content[:30]}... (length: {len(content)})")
                else:
                    # Skip unrecognized lines
                    logger.warning(f"Skipping unrecognized line: {line[:30]}...")
                    i += 1

            # If we only have the system message, add the welcome message
            if len(parsed_messages) == 1:
                parsed_messages.append(AIMessage(content=welcome_message))
                logger.info("Added welcome message as no valid messages were found")

            # Debug output
            logger.info(f"Loaded {len(parsed_messages)} messages in total")
            return parsed_messages

        logger.warning("No messages found in conversation metadata")
        return None

    except Exception as e:
        logger.error(f"Error loading conversation messages: {e}")
        return None

def initialize_conversation_chain(llm, conversation_store, session_id, system_prompt, tools):
    """Initialize the conversation chain with previous context and tools if available"""
    # Load existing conversation or get defaults
    conversation_data = load_conversation(conversation_store, session_id)

    # Format the system prompt with the conversation data
    formatted_prompt = system_prompt.format(
        history=conversation_data["messages"],
        context=conversation_data["context_summary"]
    )

    # Create a prompt with messages placeholder for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", formatted_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create the agent with tools
    agent = create_openai_tools_agent(llm, tools, prompt)

    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=3,
        handle_parsing_errors=True,
    )

    logger.info("🤖 Initialized agent with tools")
    return agent_executor
