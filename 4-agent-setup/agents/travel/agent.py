"""
Travel agent implementation.

This module defines the travel agent with its models, tools, and chain configuration.
"""

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.logger import logger
from utils.conversation import load_conversation
from utils.vector import initialize_vector_store, initialize_embedding_model
from agents.travel.tools import get_city_weather, get_city_info, get_city_fallback_info
from agents.travel.prompts import TRAVEL_SYSTEM_PROMPT, TRAVEL_WELCOME_MESSAGE

def initialize_llm(temperature=0.7, model="gpt-3.5-turbo", streaming=True):
    """Initialize and return a langchain LLM instance."""
    logger.info(f"Initializing LLM with {model} model")
    return ChatOpenAI(
        temperature=temperature,
        model=model,
        streaming=streaming
    )

def initialize_travel_tools():
    """Initialize the tools for the travel agent."""
    logger.info("Initializing travel tools")
    tools = [get_city_weather, get_city_info, get_city_fallback_info]
    return tools

def create_travel_agent(llm, conversation_store, session_id, system_prompt):
    """Create a travel agent with the LLM, tools, and conversation context.

    Args:
        llm: The language model instance
        conversation_store: The vector store for conversations
        session_id: The current session ID
        system_prompt: The system prompt to use

    Returns:
        An agent executor instance ready to process messages
    """
    logger.info("Creating travel agent")
    tools = initialize_travel_tools()

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

    logger.info("🤖 Travel agent created successfully")
    return agent_executor

def get_initializer():
    return {
        "llm": initialize_llm,
        "tools": initialize_travel_tools,
        "agent": create_travel_agent,
        "system_prompt": TRAVEL_SYSTEM_PROMPT,
        "welcome_message": TRAVEL_WELCOME_MESSAGE,
        "embedding_model": initialize_embedding_model,
        "conversation_store": {
            "initialize": initialize_vector_store,
            "persist_directory": "conversation_store",
            "collection_name": "conversations",
        },
        "knowledge_store": {
            "initialize": initialize_vector_store,
            "persist_directory": "knowledge_store",
            "collection_name": "knowledge",
        }
    }
