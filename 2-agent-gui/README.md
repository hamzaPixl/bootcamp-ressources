# City Explorer AI

A Streamlit-based chat interface for a travel assistant powered by GPT-3.5 Turbo. This application helps users plan their trips by providing detailed city itineraries and recommendations.

## Features

- Modern web interface with Streamlit
- Structured travel recommendations
- Contextual conversation flow
- Markdown-formatted responses
- Loading indicators
- Uses GPT-3.5 Turbo model
- Temperature set to 0.7 for balanced creativity/consistency
- Session-based chat history

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

## System Prompt

The assistant uses the following prompt to structure its responses:

```markdown
You are an expert travel assistant specialized in creating detailed city itineraries.
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
4. Budget constraints if relevant
```

## Response Format

For each city query, the assistant will:

1. First ask about necessary details (length of stay, interests, season, budget)
2. Then provide recommendations organized by category
3. Include specific details for each recommendation:
   - Brief description
   - Best time to visit
   - Time needed
   - Special tips

## Technical Details

- Built with LangChain framework
- Uses ChatOpenAI for model interaction
- Streaming enabled for smooth responses
- Maintains chat history during session
- Markdown formatting for structured responses
- Streamlit for web interface and state management
