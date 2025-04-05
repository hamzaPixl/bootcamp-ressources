# 🌆 City Explorer AI

A simple travel assistant chatbot that helps you plan trips to cities around the world.

## What it does

- **Travel recommendations**: Get suggestions for landmarks, food, activities and more for any city
- **Real-time information**: Searches the web for current data about attractions
- **Remembers conversations**: Saves your chat history to pick up where you left off

## How it works

- **LangChain + GPT-3.5**: Powers the conversational abilities
- **Web Search**: Uses DuckDuckGo for up-to-date information
- **Chat Memory**: Stores conversations in a JSON file
- **Streamlit**: Provides the simple chat interface

## Getting started

1. Install requirements:

   ```
   pip install -r requirements.txt
   ```

2. Set up your OpenAI API key:

   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file

3. Run the app:
   ```
   streamlit run start.py
   ```

## Using the app

1. Type any city name to start planning
2. Ask about specific interests, budget, or duration
3. Get structured recommendations for your trip
4. Continue the conversation to refine suggestions
