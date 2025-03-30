from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os

def main():
    load_dotenv()

    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
    chat_history = []

    agent = initialize_agent(
        tools=[],
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        early_stopping_method="generate",
        handle_parsing_errors=True
    )

    # Add system message
    agent.agent.llm_chain.prompt.messages[0] = SystemMessage(content="You are a helpful AI assistant.")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            break
        response = agent.run({"input": user_input, "chat_history": chat_history})
        chat_history.extend([
            HumanMessage(content=user_input),
            AIMessage(content=response)
        ])
        print(f"Assistant: {response}")

if __name__ == "__main__":
    main()
