from langchain.schema import SystemMessage, AIMessage, HumanMessage
from utils.logger import logger

def process_message_for_agent(messages):
    """Process messages to be used by the agent.

    Args:
        messages: A list of message objects

    Returns:
        A list of messages in the format expected by the agent
    """
    logger.info("Processing messages for agent")

    # Filter out system messages for the agent input
    filtered_messages = [
        m for m in messages
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

    logger.info(f"Processed {len(agent_messages)} messages for agent")
    return agent_messages

def create_ai_message(content):
    """Create an AI message object.

    Args:
        content: The message content

    Returns:
        An AIMessage object
    """
    return AIMessage(content=content)

def create_system_message(content):
    """Create a system message object.

    Args:
        content: The message content

    Returns:
        A SystemMessage object
    """
    return SystemMessage(content=content)

def create_initial_messages(system_prompt, welcome_message):
    """Create the initial messages for a new conversation.

    Args:
        system_prompt: The system prompt
        welcome_message: The welcome message

    Returns:
        A list of message objects
    """
    return [
        create_system_message(system_prompt),
        create_ai_message(welcome_message)
    ]
