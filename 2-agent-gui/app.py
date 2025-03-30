import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os

SYSTEM_PROMPT = """You are an expert travel assistant specialized in creating detailed city itineraries.
When a user mentions a city, provide a well-structured list of activities and places to visit, organized by these categories:
- Must-See Landmarks & Attractions
- Cultural Experiences
- Food & Dining Recommendations
- Local Hidden Gems
- Nature & Outdoor Activities (if applicable)
- Shopping Districts
- Evening/Nightlife Suggestions

For each category:
1. List 2-3 specific places or activities
2. Include brief descriptions (1-2 sentences)
3. Mention best time to visit or any special tips
4. If relevant, suggest approximate time needed

Keep responses concise but informative. If asked about specific interests or time constraints, adjust recommendations accordingly.

Always start by asking about:
1. Length of stay if not mentioned
2. Any specific interests
3. Travel season/time of year
4. Budget constraints if relevant"""

WELCOME_MESSAGE = """👋 Welcome to City Explorer AI! I'm your personal travel assistant.

To get started, simply tell me which city you'd like to explore. I'll help you create the perfect itinerary by:
- Suggesting must-see landmarks and attractions
- Recommending local food and dining spots
- Finding hidden gems and local favorites
- Planning cultural experiences
- Suggesting outdoor activities
- Recommending shopping areas
- Planning evening entertainment

Just type the name of any city, and I'll guide you through creating your perfect itinerary!"""

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            AIMessage(content=WELCOME_MESSAGE)
        ]
    if "llm" not in st.session_state:
        load_dotenv()
        st.session_state.llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            streaming=True
        )

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
    for message in st.session_state.messages[1:]:  # Skip system message
        with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
            st.markdown(message.content)

    # Chat input
    if user_input := st.chat_input("Tell me which city you'd like to explore..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user message to chat history
        st.session_state.messages.append(HumanMessage(content=user_input))

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Planning your perfect day..."):
                messages = st.session_state.messages.copy()
                response = st.session_state.llm.invoke([msg for msg in messages]).content
                st.markdown(response)

        # Add AI response to chat history
        st.session_state.messages.append(AIMessage(content=response))

if __name__ == "__main__":
    main()
