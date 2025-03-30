# City Explorer AI with Memory and Tools

An enhanced version of the City Explorer AI that includes conversation memory and web search capabilities. This agent maintains conversation history and can search for current information about destinations.

## New Features

- **Conversation Memory**: Maintains context throughout the conversation
- **Web Search Integration**: Uses DuckDuckGo to find current information about:
  - Attractions and landmarks
  - Events and temporary exhibitions
  - Current pricing and opening hours
  - Special tips and travel advisories
- **Enhanced Responses**: Combines AI knowledge with real-time information
- **Persistent Context**: Remembers previous questions and preferences

## Prerequisites

- Python 3.x
- OpenAI API key

## Setup

1. Clone the repository
2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to `.env`:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

The web interface will automatically open in your default browser. If it doesn't, you can manually navigate to the URL shown in the terminal (usually http://localhost:8501).

## Features

- Modern web interface with Streamlit
- Real-time web search integration
- Conversation memory for context
- Current information about destinations
- Well-structured travel recommendations
- Loading indicators for responses
- Uses GPT-3.5 Turbo model
- Temperature set to 0.7 for balanced creativity/consistency
- Persistent chat history during session

## Technical Details

- Built with LangChain framework
- Uses ChatOpenAI for model interaction
- Implements CHAT_CONVERSATIONAL_REACT_DESCRIPTION agent type
- ConversationBufferMemory for chat history
- DuckDuckGo search tool integration
- Markdown formatting for responses
- Streamlit for web interface and state management
