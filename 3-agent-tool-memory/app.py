import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import json
import os

# Add ChatHistory models
class Message(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatHistory(BaseModel):
    messages: List[Message]

class ChatHistoryManager:
    def __init__(self, history_file: str = "chat_history.json"):
        self.history_file = history_file
        self.history: ChatHistory = self._load_history()

    def _load_history(self) -> ChatHistory:
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                return ChatHistory(**data)
        return ChatHistory(messages=[])

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(
                self.history.model_dump(),
                f, indent=2
            )

    def add_message(self, role: str, content: str):
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self.history.messages.append(message)
        self.save_history()

    def get_context(self, max_messages: int = 10) -> str:
        if not self.history.messages:
            return ""

        recent_messages = self.history.messages[-max_messages:]
        context = "\n\nPrevious conversation:\n"
        for msg in recent_messages:
            context += f"{msg.role}: {msg.content}\n"
        return context

class Recommendation(BaseModel):
    name: str = Field(..., description="Name of the place or activity")
    description: str = Field(..., description="Brief description of the place or activity")
    best_time: str = Field(..., description="Best time to visit or experience this")
    duration: str = Field(..., description="Approximate time needed")
    tips: Optional[str] = Field(None, description="Special tips or notes")
    current_status: Optional[str] = Field(None, description="Any temporary closures or special events")

class CityRecommendations(BaseModel):
    city: str = Field(..., description="Name of the city")
    landmarks: List[Recommendation] = Field(..., description="Must-see landmarks and attractions")
    cultural: List[Recommendation] = Field(..., description="Cultural experiences")
    food: List[Recommendation] = Field(..., description="Food and dining recommendations")
    hidden_gems: List[Recommendation] = Field(..., description="Local hidden gems")
    nature: Optional[List[Recommendation]] = Field(None, description="Nature and outdoor activities")
    shopping: List[Recommendation] = Field(..., description="Shopping districts")
    nightlife: List[Recommendation] = Field(..., description="Evening/nightlife suggestions")

    def to_markdown(self) -> str:
        md = f"# {self.city} Recommendations\n\n"

        sections = [
            ("## Must-See Landmarks & Attractions", self.landmarks),
            ("## Cultural Experiences", self.cultural),
            ("## Food & Dining Recommendations", self.food),
            ("## Local Hidden Gems", self.hidden_gems),
            ("## Nature & Outdoor Activities", self.nature),
            ("## Shopping Districts", self.shopping),
            ("## Evening/Nightlife Suggestions", self.nightlife)
        ]

        for title, items in sections:
            if items:  # Skip empty sections
                md += f"{title}\n\n"
                for item in items:
                    md += f"### {item.name}\n"
                    md += f"- **Description**: {item.description}\n"
                    md += f"- **Best Time**: {item.best_time}\n"
                    md += f"- **Duration**: {item.duration}\n"
                    if item.tips:
                        md += f"- **Tips**: {item.tips}\n"
                    if item.current_status:
                        md += f"- **Current Status**: {item.current_status}\n"
                    md += "\n"

        return md

SYSTEM_PROMPT = """You are an expert travel assistant specialized in creating detailed city itineraries.
Your responses should ALWAYS be in valid JSON format following this structure:

```json
    city: City Name,
    landmarks: [
            name: Landmark Name,
            description: Brief description of the place,
            best_time: Best time to visit,
            duration: Time needed,
            tips: Special tips or insider advice,
            current_status: Any temporary changes or events
    ],
    cultural: [
            name: Cultural Activity,
            description: What makes it special,
            best_time: Ideal timing,
            duration: How long to plan,
            tips: Local insights,
            current_status: Current conditions
    ],
    food: [...],
    hidden_gems: [...],
    nature: [...],
    shopping: [...],
    nightlife: [...]
```

Before providing recommendations, ALWAYS ask about:
1. Length of stay if not mentioned
2. Any specific interests
3. Travel season/time of year
4. Budget constraints if relevant

When these questions haven't been answered, respond with a simple text message asking for these details.
When providing recommendations, ensure each category has 2-3 items with current information from your search results.
Format all responses either as plain text questions or valid JSON matching the above structure.

Context:
{context}"""

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

    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatHistoryManager()

    if "current_city" not in st.session_state:
        st.session_state.current_city = None

    if "agent" not in st.session_state:
        load_dotenv()

        llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
        search = DuckDuckGoSearchRun()
        tools = [search]

        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )

        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

        # Initialize with base prompt
        system_prompt = SYSTEM_PROMPT.format(context="")
        agent.agent.llm_chain.prompt.messages[0] = SystemMessage(content=system_prompt)
        st.session_state.agent = agent

def extract_city_from_input(user_input: str) -> Optional[str]:
    # This is a simple implementation - you might want to use NLP for better city extraction
    # For now, we'll assume the first capitalized word is the city
    words = user_input.split()
    for word in words:
        if word[0].isupper():
            return word
    return None

def format_response(response: str) -> str:
    try:
        # Try to parse as JSON
        data = json.loads(response)
        recommendations = CityRecommendations(**data)
        return recommendations.to_markdown()
    except (json.JSONDecodeError, ValueError):
        # If not JSON, return as is (probably a question for more details)
        return response

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

        # Get context from chat history
        context = st.session_state.chat_manager.get_context()

        print(context)
        # Update system prompt with context
        st.session_state.agent.agent.llm_chain.prompt.messages[0] = SystemMessage(
            content=SYSTEM_PROMPT.format(context=context)
        )

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Researching and planning your perfect trip..."):
                response = st.session_state.agent.run({"input": user_input})
                formatted_response = format_response(response)
                st.markdown(formatted_response)

        # Update message history
        st.session_state.messages.extend([
            HumanMessage(content=user_input),
            AIMessage(content=formatted_response)
        ])

        # Save to local history
        st.session_state.chat_manager.add_message(
            role="user",
            content=user_input
        )
        st.session_state.chat_manager.add_message(
            role="assistant",
            content=formatted_response
        )

if __name__ == "__main__":
    main()
