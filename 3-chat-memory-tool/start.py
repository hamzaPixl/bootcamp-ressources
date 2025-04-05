import streamlit as st
import os
import uuid
import logging
import sys
import datetime
import colorama
import requests
from colorama import Fore, Style
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.documents import Document
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Initialize colorama
colorama.init(autoreset=True)

# Custom logging formatter with colors and emojis
class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "🔍 %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "ℹ️ %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "⚠️ %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "❌ %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.MAGENTA + "🚨 %(message)s" + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure logging with custom formatter
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ColoredFormatter())
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Log only essential environment info
logger.info(f"Starting City Explorer AI application")

# Define the weather tool
@tool
def get_city_weather(city: str) -> str:
    """Get the current weather for a specific city.

    Args:
        city: The name of the city to get weather for.

    Returns:
        A string with current weather information for the city.
    """
    logger.info(f"🌡️ Getting weather for {city}")

    try:
        # Use OpenWeatherMap API - you'd need to set OPENWEATHER_API_KEY in your .env file
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            logger.warning("No OpenWeather API key found in environment variables")
            return f"I couldn't retrieve current weather for {city} due to missing API key."

        # Call weather API
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']

            weather_info = f"Current weather in {city}:\n"
            weather_info += f"- Conditions: {weather_desc}\n"
            weather_info += f"- Temperature: {temp}°C\n"
            weather_info += f"- Humidity: {humidity}%\n"
            weather_info += f"- Wind Speed: {wind_speed} m/s"

            logger.info(f"✅ Weather retrieved successfully for {city}")
            return weather_info
        else:
            logger.warning(f"Weather API error: {response.status_code} - {response.text}")
            return f"I couldn't retrieve current weather for {city}. The city might not be found or there's an API issue."

    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        return f"I encountered an error while getting weather for {city}."

# Define city information tool
@tool
def get_city_info(city: str) -> str:
    """Get general information and top attractions about a specific city.

    Args:
        city: The name of the city to get information for.

    Returns:
        A string with information about the city and its top attractions.
    """
    logger.info(f"🏙️ Getting info for {city}")

    try:
        # Use OpenTripMap API to get city data
        # You'll need to get a free API key from https://opentripmap.io/
        api_key = os.getenv("OPENTRIPMAP_API_KEY")

        # First, get the city coordinates
        geoname_url = f"https://api.opentripmap.com/0.1/en/places/geoname?name={city}&apikey={api_key}"
        geo_response = requests.get(geoname_url)

        if geo_response.status_code != 200:
            logger.warning(f"OpenTripMap API error: {geo_response.status_code} - {geo_response.text}")
            return get_city_fallback_info(city)

        geo_data = geo_response.json()
        if not geo_data or "lat" not in geo_data or "lon" not in geo_data:
            logger.warning(f"Could not find coordinates for {city}")
            return get_city_fallback_info(city)

        # Get city information and attractions using the coordinates
        lat = geo_data["lat"]
        lon = geo_data["lon"]
        country = geo_data.get("country", "")

        # Get the top attractions
        radius = 5000  # 5km radius
        limit = 10     # Top 10 attractions
        attractions_url = f"https://api.opentripmap.com/0.1/en/places/radius?radius={radius}&lon={lon}&lat={lat}&rate=3&format=json&limit={limit}&apikey={api_key}"
        attractions_response = requests.get(attractions_url)

        if attractions_response.status_code != 200:
            logger.warning(f"OpenTripMap attractions API error: {attractions_response.status_code}")
            return get_city_fallback_info(city)

        attractions_data = attractions_response.json()

        # Format the response
        city_info = f"# {city.title()}, {country}\n\n"
        city_info += f"{city.title()} is located at coordinates {lat:.2f}, {lon:.2f}. "

        if geo_data.get("population"):
            city_info += f"It has a population of approximately {geo_data['population']:,}. "

        city_info += "\n\n## Top Attractions:\n\n"

        if not attractions_data:
            city_info += "No specific attractions found in the database for this city.\n"
        else:
            for i, attraction in enumerate(attractions_data[:6], 1):
                name = attraction.get("name", "Unnamed attraction")
                kinds = attraction.get("kinds", "").replace(",", ", ")

                # Skip attractions without names
                if not name or name == "":
                    continue

                city_info += f"{i}. **{name}**\n"
                if kinds:
                    city_info += f"   - Type: {kinds}\n"
                if attraction.get("rate"):
                    city_info += f"   - Rating: {attraction.get('rate', 0)}/7\n"
                city_info += "\n"

        logger.info(f"✅ Retrieved {len(attractions_data) if attractions_data else 0} attractions for {city}")
        return city_info

    except Exception as e:
        logger.error(f"Error getting city info: {str(e)}")
        return get_city_fallback_info(city)

def get_city_fallback_info(city: str) -> str:
    """Fallback function for city information when API fails"""
    # Simplified mock function with basic city information
    city_info = {
        "paris": "Paris is the capital of France, known for the Eiffel Tower, Louvre Museum, and exquisite cuisine. The city experiences a temperate climate with mild summers and cool winters.",
        "london": "London is the capital of the UK, famous for Big Ben, Buckingham Palace, and its rich history. The city often has rainy weather throughout the year.",
        "new york": "New York City is the largest city in the USA, famous for Times Square, Central Park, and the Statue of Liberty. It has hot summers and cold winters with occasional snowfall.",
        "tokyo": "Tokyo is Japan's capital and the world's most populous metropolis. It's known for its technology, cuisine, and blend of traditional and ultramodern culture.",
        "rome": "Rome is Italy's capital and a historic city known for the Colosseum, Vatican City, and delicious Italian cuisine. It has hot, dry summers and mild, rainy winters."
    }

    city_lower = city.lower()
    if city_lower in city_info:
        return city_info[city_lower]
    else:
        # Fall back to a generic response
        return f"{city} is a city that travelers often visit. Consider researching its main attractions, local cuisine, and cultural highlights before planning your visit."

# Updated system prompt to include weather tool information
SYSTEM_PROMPT = """You are an expert travel assistant specialized in creating detailed city itineraries.

You have access to tools that can provide you with:
1. Current weather conditions for any city (get_city_weather)
2. City information with top attractions (get_city_info)

When a user asks about a city or requests an itinerary, you should automatically use the appropriate tool to enhance your response with relevant information.

History: {history}

Context: {context}

When a user mentions a city, create a well-structured list of activities and places to visit, organized by these categories:
- Must-See Landmarks & Attractions (use the attractions from get_city_info)
- Cultural Experiences
- Food & Dining Recommendations
- Local Hidden Gems
- Nature & Outdoor Activities (if applicable)
- Shopping Districts
- Evening/Nightlife Suggestions

Include the current weather information at the beginning of your response to help the user plan accordingly.

For each category:
1. List 2-3 specific places or activities
2. Include brief descriptions (1-2 sentences)
3. Mention best time to visit or any special tips
4. If relevant, suggest approximate time needed

Keep responses concise but informative. If asked about specific interests or time constraints, adjust recommendations accordingly.

Format your responses using markdown to make them organized and easy to read.
"""

WELCOME_MESSAGE = """👋 Welcome to City Explorer AI! I'm your personal travel assistant.

To get started, simply tell me which city you'd like to explore. I'll help you create the perfect itinerary by:
- Finding top attractions and landmarks using real-time data
- Recommending local food and dining spots
- Finding hidden gems and local favorites
- Planning cultural experiences
- Suggesting outdoor activities
- Recommending shopping areas
- Planning evening entertainment
- Providing current weather information to help plan your day

Just type the name of any city, and I'll guide you through creating your perfect itinerary!"""

load_dotenv()

def initialize_tools():
    """Initialize the tools for the LLM"""
    tools = [get_city_weather, get_city_info]
    return tools

def initialize_conversation_chain(llm, conversation_store, session_id):
    """Initialize the conversation chain with previous context and tools if available"""
    # Load existing conversation or get defaults
    conversation_data = load_conversation(conversation_store, session_id)

    # Get tools
    tools = initialize_tools()

    # Format the system prompt with the conversation data
    formatted_prompt = SYSTEM_PROMPT.format(
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

def initialize_embedding_model():
    return OpenAIEmbeddings()

def initialize_vector_store(embedding_model, persist_directory="vector_store", collection_name="documents"):
    """Initialize vector store for conversation tracking"""
    # Create a shared directory for all collections
    os.makedirs(persist_directory, exist_ok=True)

    # Initialize conversation store for tracking conversation history
    conversation_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_directory
    )
    logger.info(f"🗃️ Initialized vector store: {collection_name}")
    return conversation_store

def initialize_llm():
    return ChatOpenAI(
        temperature=0.7,
        model="gpt-3.5-turbo",
        streaming=True
    )

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
        results = conversation_store.get(
            where={"session_id": session_id}
        )

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
    conversation_store.add_documents([
        Document(page_content=content_text, metadata=metadata)
    ])

    logger.info(f"✅ Conversation saved successfully (ID: {session_id[:8]}...)")
    return session_id

def initialize_session_state():
    # Generate a new session ID if not already set
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logger.info(f"🆕 Created new session: {st.session_state.session_id[:8]}...")

    # Initialize LLM if not already done
    if "llm" not in st.session_state:
        st.session_state.llm = initialize_llm()

    # Initialize embedding model and stores
    if "embedding_model" not in st.session_state:
        st.session_state.embedding_model = initialize_embedding_model()

    if "conversation_store" not in st.session_state:
        st.session_state.conversation_store = initialize_vector_store(
            st.session_state.embedding_model,
            'conversation_store',
            'conversations'
        )

    if "knowledge_store" not in st.session_state:
        st.session_state.knowledge_store = initialize_vector_store(
            st.session_state.embedding_model,
            'knowledge_store',
            'knowledge'
        )

    # Initialize messages array if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            AIMessage(content=WELCOME_MESSAGE)
        ]

    # Initialize conversation chain last, after all dependencies are set up
    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = initialize_conversation_chain(
            st.session_state.llm,
            st.session_state.conversation_store,
            st.session_state.session_id
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

                # Filter out system messages for the agent input
                filtered_messages = [
                    m for m in st.session_state.messages
                    if not isinstance(m, SystemMessage)
                ][-5:]  # Only use the last 5 messages for context

                # Convert LangChain message objects to dict format expected by the agent
                agent_messages = []
                for m in filtered_messages:
                    if isinstance(m, HumanMessage):
                        agent_messages.append({"role": "user", "content": m.content})
                    elif isinstance(m, AIMessage):
                        if isinstance(m.content, str):
                            agent_messages.append({"role": "assistant", "content": m.content})
                        else:
                            # Handle dict content
                            agent_messages.append({"role": "assistant", "content": str(m.content)})

                logger.info(f"Sending {len(agent_messages)} messages to agent")

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

def get_saved_conversations(conversation_store):
    """Get a list of saved conversations from the store"""
    try:
        # Get all documents from the store
        results = conversation_store.get()

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
        results = conversation_store.get(
            where={"session_id": session_id}
        )

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

def load_conversation_messages(conversation_store, session_id):
    """Load the messages for a specific conversation as message objects"""
    try:
        results = conversation_store.get(
            where={"session_id": session_id}
        )

        if not results or not results.get('metadatas') or len(results['metadatas']) == 0:
            logger.warning(f"❓ No conversation found with ID: {session_id[:8]}...")
            return None

        metadata = results['metadatas'][0]
        if "messages" in metadata:
            messages_text = metadata["messages"]
            logger.info(f"Raw messages from store:\n{messages_text[:200]}..." if len(messages_text) > 200 else messages_text)

            # Convert text back to message objects
            parsed_messages = [SystemMessage(content=SYSTEM_PROMPT)]

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
                parsed_messages.append(AIMessage(content=WELCOME_MESSAGE))
                logger.info("Added welcome message as no valid messages were found")

            # Debug output
            logger.info(f"Loaded {len(parsed_messages)} messages in total")
            return parsed_messages

        logger.warning("No messages found in conversation metadata")
        return None

    except Exception as e:
        logger.error(f"Error loading conversation messages: {e}")
        return None

def main():
    logger.info("🚀 Starting City Explorer AI")
    load_dotenv()

    st.set_page_config(
        page_title="City Explorer AI",
        page_icon="🌆",
        layout="centered"
    )

    st.title("🌆 City Explorer AI")
    st.caption("Your personal travel assistant for discovering the best of any city")

    try:
        # Initialize the session state - must happen first
        initialize_session_state()

        # Render existing chat messages
        render_chat()

        # Add sidebar
        st.sidebar.title("Chat Controls")

        # Create a new conversation button
        if st.sidebar.button("➕ New Conversation"):
            logger.info("🆕 Starting new conversation")
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                AIMessage(content=WELCOME_MESSAGE)
            ]
            st.session_state.conversation_chain = initialize_conversation_chain(
                st.session_state.llm,
                st.session_state.conversation_store,
                st.session_state.session_id
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
            st.session_state.messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                AIMessage(content=WELCOME_MESSAGE)
            ]
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
                        conv['id']
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

        # Handle new user input
        if prompt := st.chat_input("Enter a city name"):
            handle_user_input(prompt)

    except Exception as e:
        error_msg = f"Application error: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)

        # Make sure messages are initialized
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Add error message to chat
        st.session_state.messages.append(AIMessage(content=f"⚠️ {error_msg}"))
        st.rerun()

if __name__ == "__main__":
    main()
