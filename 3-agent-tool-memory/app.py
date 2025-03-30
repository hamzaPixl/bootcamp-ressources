import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
import os

WELCOME_MESSAGE = """👋 Welcome to City Explorer AI! I'm your personal travel assistant.

To get started, simply tell me which city you'd like to explore. I'll help you create the perfect itinerary by:
- Suggesting must-see landmarks and attractions
- Recommending local food and dining spots
- Finding hidden gems and local favorites
- Planning cultural experiences
- Suggesting outdoor activities
- Recommending shopping areas
- Planning evening entertainment

I can also search the web for up-to-date information about attractions, events, and travel tips!
Just type the name of any city, and I'll guide you through creating your perfect itinerary!"""

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [AIMessage(content=WELCOME_MESSAGE)]

    if "agent" not in st.session_state:
        load_dotenv()

        # Initialize the LLM
        llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

        # Initialize tools
        search = DuckDuckGoSearchRun()
        tools = [
            search
        ]

        # Initialize memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )

        # Initialize the agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

        # Set the system message
        agent.agent.llm_chain.prompt.messages[0] = SystemMessage(
            content="""You are an expert travel assistant specialized in creating detailed city itineraries.
Your responses should ALWAYS be well-structured and formatted in Markdown.
Use your search tool to find current information about attractions, events, and travel tips.

When a user mentions a city, search for current information and then provide recommendations organized by these categories:

## Must-See Landmarks & Attractions
## Cultural Experiences
## Food & Dining Recommendations
## Local Hidden Gems
## Nature & Outdoor Activities (if applicable)
## Shopping Districts
## Evening/Nightlife Suggestions

For each category:
1. List 2-3 specific places or activities with CURRENT information
2. Include brief descriptions (1-2 sentences)
3. Mention best time to visit or any special tips
4. If relevant, suggest approximate time needed and current pricing
5. Note any temporary closures or special events

Before providing recommendations, ALWAYS ask about:
1. Length of stay if not mentioned
2. Any specific interests
3. Travel season/time of year
4. Budget constraints if relevant

Keep responses informative but concise. Format all responses in clear Markdown with proper headers and bullet points.
When searching for information, focus on recent and reliable sources."""
        )

        st.session_state.agent = agent

def main():
    st.set_page_config(
        page_title="City Explorer AI",
        page_icon="🌆",
        layout="centered"
    )

    st.title("🌆 City Explorer AI")
    st.caption("Your personal travel assistant for discovering the best of any city")

    initialize_session_state()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
            st.markdown(message.content)

    # Chat input
    if user_input := st.chat_input("Tell me which city you'd like to explore..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Researching and planning your perfect trip..."):
                response = st.session_state.agent.run({"input": user_input})
                st.markdown(response)

        # Update message history
        st.session_state.messages.extend([
            HumanMessage(content=user_input),
            AIMessage(content=response)
        ])

if __name__ == "__main__":
    main()
