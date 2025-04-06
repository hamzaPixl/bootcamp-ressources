import streamlit as st
from dotenv import load_dotenv

from utils.logger import logger
from utils.streamlit import initialize_session_state, render_chat, handle_user_input, setup_sidebar
from agents.travel import get_initializer

load_dotenv()

def main():
    logger.info("🚀 Starting City Explorer AI")

    st.set_page_config(
        page_title="City Explorer AI",
        page_icon="🌆",
        layout="centered"
    )

    st.title("🌆 City Explorer AI")
    st.caption("Your personal travel assistant for discovering the best of any city")

    try:
        travel_initializer = get_initializer()

        # Initialize the session state - must happen first
        initialize_session_state(travel_initializer)

        # Render existing chat messages
        render_chat()

        # Setup sidebar with conversation controls
        setup_sidebar(travel_initializer)

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
        from langchain.schema import AIMessage
        st.session_state.messages.append(AIMessage(content=f"⚠️ {error_msg}"))
        st.rerun()

if __name__ == "__main__":
    main()
