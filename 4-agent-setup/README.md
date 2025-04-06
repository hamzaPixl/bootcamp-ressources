# 🌆 City Explorer AI

A travel assistant chatbot that helps you plan trips to cities around the world, powered by LangChain and OpenAI's models.

## 🌟 Features

- **City information**: Get detailed information about any city worldwide
- **Weather updates**: Real-time weather data for travel planning
- **Smart recommendations**: Curated lists of attractions, dining, and activities
- **Conversation memory**: System remembers your previous interactions
- **Extensible architecture**: Modular design allows easy addition of new tools and capabilities

## 🏗️ Architecture

The City Explorer AI uses a modular, layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                       │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                      Agent Layer                             │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Travel Agent   │  │  Other       │  │  Future        │  │
│  │  - init         │  │  Specialized │  │  Extension     │  │
│  │  - tools        │  │  Agents      │  │  Agents        │  │
│  │  - prompts      │  │              │  │                │  │
│  └────────┬────────┘  └──────────────┘  └────────────────┘  │
└───────────┼──────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────┐
│                    Utility Layer                              │
│  ┌─────────────┐ ┌───────────────┐ ┌────────────────────┐    │
│  │ Conversation│ │ Vector Store  │ │ Messaging/Logging  │    │
│  │ Management  │ │ Operations    │ │ Utilities          │    │
│  └─────────────┘ └───────────────┘ └────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Components:

1. **Streamlit UI Layer**: Manages the user interface, chat display, and session state
2. **Agent Layer**: Contains specialized AI agents with their tools and prompt templates
3. **Utility Layer**: Provides shared functionality like conversation storage, vector operations, and logging

## 🛠️ Stack & Technologies

- **LangChain**: Framework for building LLM applications
- **OpenAI Models**: Powers the intelligent responses (gpt-3.5-turbo default)
- **Streamlit**: Web interface for chat interaction
- **Chroma DB**: Vector store for conversation memory
- **External APIs**:
  - OpenWeatherMap: For real-time weather data
  - OpenTripMap: For city information and attractions

## 📂 Project Structure

```
city-explorer/
├── agents/                    # Agent definitions and implementations
│   ├── __init__.py           # Root agent package exports
│   └── travel/               # Travel agent implementation
│       ├── __init__.py       # Travel agent exports
│       ├── agent.py          # Travel agent core functionality
│       ├── prompts.py        # Travel-specific prompt templates
│       └── tools/            # Travel-specific tools
│           ├── __init__.py   # Tool exports
│           ├── city_info.py  # City information tool
│           └── weather.py    # Weather data tool
├── utils/                    # Shared utility functions
│   ├── __init__.py           # Utilities exports
│   ├── conversation.py       # Conversation management
│   ├── logger.py             # Logging configuration
│   ├── messaging.py          # Message processing
│   ├── streamlit.py          # Streamlit UI helpers
│   └── vector.py             # Vector store operations
├── start.py                  # Application entry point
├── .env                      # Environment variables (API keys)
├── .gitignore                # Git ignore file
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🔄 Data Flow

1. **User Input**: User enters text in the Streamlit interface
2. **Message Processing**: Input is processed into LangChain message format
3. **Tool Selection**: The agent determines which tool(s) to use for the query
4. **API Requests**: Tools make external API calls as needed
5. **Response Generation**: The agent combines API data with its own knowledge
6. **Conversation Storage**: Interactions are stored in the vector database
7. **UI Rendering**: Response is displayed to the user in the chat interface

## 🧠 Agent System

The system uses the concept of "agents" - specialized AI assistants with access to specific tools:

### Travel Agent

The primary agent that handles city exploration requests:

- **Tools**:

  - `get_city_weather`: Fetches current weather conditions using OpenWeatherMap API
  - `get_city_info`: Retrieves city data and attractions using OpenTripMap API
  - `get_city_fallback_info`: Provides generic information when APIs fail

- **Initialization**:
  The agent is initialized with:
  - LLM (Language Model)
  - Conversation memory store
  - System prompt template
  - Tool set

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- OpenWeatherMap API key
- OpenTripMap API key

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/city-explorer.git
   cd city-explorer
   ```

2. Install requirements:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` to add your API keys:

   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENWEATHER_API_KEY=your_openweather_api_key
   OPENTRIPMAP_API_KEY=your_opentripmap_api_key
   ```

4. Run the application:
   ```bash
   streamlit run start.py
   ```

### Usage

1. Enter a city name in the chat input (e.g., "Tell me about Paris")
2. The assistant will respond with city information, weather, and recommendations
3. Ask follow-up questions to refine recommendations or explore other aspects
4. Use the sidebar to:
   - Start a new conversation
   - Save the current conversation
   - Clear the conversation
   - Load a previously saved conversation

## 🔧 Extending the System

### Adding New Tools

1. Create a new tool file in `agents/travel/tools/`
2. Define functions with the `@tool` decorator from LangChain
3. Update `initialize_travel_tools()` in `agents/travel/agent.py`

### Creating New Agents

1. Create a new directory in `agents/` for your specialized agent
2. Implement the agent with its own tools and prompts
3. Export the agent through the appropriate `__init__.py` files
4. Update the UI to accommodate the new agent

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for the LLM framework
- [Streamlit](https://streamlit.io/) for the UI components
- [OpenAI](https://openai.com/) for the language models
- [OpenWeatherMap](https://openweathermap.org/) for weather data
- [OpenTripMap](https://opentripmap.io/) for city information
