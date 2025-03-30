# Simple Chat Agent

A basic conversational agent built with LangChain and GPT-3.5 Turbo. This agent maintains conversation history and provides a simple command-line interface for interaction.

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

Run the chat agent:

```bash
python app.py
```

- Type your messages and press Enter to chat
- Type 'quit', 'exit', or 'bye' to end the conversation

## Features

- Uses GPT-3.5 Turbo model
- Maintains conversation history
- Temperature set to 0.7 for balanced creativity/consistency
- Simple command-line interface
- Graceful exit commands

## Technical Details

- Built with LangChain framework
- Uses ChatOpenAI for model interaction
- Implements CHAT_CONVERSATIONAL_REACT_DESCRIPTION agent type
- Handles message history with proper typing (HumanMessage/AIMessage)
