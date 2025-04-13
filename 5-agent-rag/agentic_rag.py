# import basics
import os
from dotenv import load_dotenv
import traceback

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings

from supabase import create_client, Client

# load environment variables
load_dotenv()

def log_error(e: Exception, context: str):
    """Log error with context and stack trace."""
    print(f"\n❌ Error in {context}:")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nStack trace:")
    print(traceback.format_exc())

@tool
def retrieve(query: str) -> str:
    """Retrieve relevant documents for a query."""
    try:
        # Initialize vector store
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = SupabaseVectorStore(
            embedding=embeddings,
            client=create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_KEY")
            ),
            table_name="documents_new",
            query_name="match_documents"
        )

        # Perform similarity search
        results = vector_store.similarity_search(query, k=3)

        if not results:
            return "No relevant documents found."

        # Format results
        response = "Relevant documents found:\n\n"
        for i, doc in enumerate(results, 1):
            response += f"Document {i}:\n"
            response += f"Content: {doc.page_content[:500]}...\n"
            response += f"Source: {doc.metadata.get('filename', 'Unknown')}\n"
            response += f"Page: {doc.metadata.get('page', 'N/A')}\n\n"

        return response

    except Exception as e:
        log_error(e, "Document retrieval")
        return "Error retrieving documents."

def create_agent():
    """Create and return an agent for document retrieval."""
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0
        )

        # Define tools
        tools = [retrieve]

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
             You are a helpful assistant that answers questions based on document content.
             When asked a question:
             1. Use the retrieve tool to find relevant documents
             2. Provide a concise answer based on the documents
             3. Cite your sources
             4. If you're unsure, say so
             """),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        agent = create_openai_functions_agent(llm, tools, prompt)

        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True
        )

        return agent_executor

    except Exception as e:
        log_error(e, "Agent creation")
        raise

def main():
    """Main function to run the agent."""
    try:
        print("Initializing document retrieval agent...")

        # Create agent
        agent = create_agent()

        # Interactive loop
        print("\nAsk questions about the documents (type 'quit' to exit):")
        while True:
            query = input("\nYour question: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if not query:
                continue

            try:
                response = agent.invoke({"input": query})
                print("\nResponse:", response['output'])

            except Exception as e:
                log_error(e, "Query processing")
                continue

    except Exception as e:
        log_error(e, "Main execution")
        raise

if __name__ == "__main__":
    main()
