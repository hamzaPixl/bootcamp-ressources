"""
Agent definitions and components for the City Explorer application.

This package contains:
- Agent definitions and configuration
- LLM model setup
- Tool definitions and implementations
- Prompt templates
"""

from agents.travel import (
    initialize_llm,
    initialize_travel_tools,
    create_travel_agent,
    get_initializer
)

# Export the travel agent components
__all__ = [
    'initialize_llm',
    'initialize_travel_tools',
    'create_travel_agent',
    'get_initializer'
]

__version__ = "0.1.0"
