# import basics
import os
from dotenv import load_dotenv
import traceback

from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase import create_client, Client

# load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def log_error(e: Exception, context: str):
    """Log error with context and stack trace."""
    print(f"\n❌ Error in {context}:")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nStack trace:")
    print(traceback.format_exc())

def test_database_connection():
    """Test database connection and table structure."""
    try:
        print("\n1. Testing Database Connection...")

        # Test connection
        result = supabase.table('documents_new').select('count').execute()
        print("✓ Connected to Supabase")

        # Check tables
        tables = ['documents_new', 'document_chunks', 'documents']
        for table in tables:
            try:
                count = supabase.table(table).select('count').execute()
                print(f"✓ Table '{table}' exists")
            except Exception:
                print(f"✗ Table '{table}' does not exist")

        # Get counts
        try:
            chunks_count = supabase.table('document_chunks').select('count').execute()
            print(f"Document chunks count: {chunks_count.data[0]['count']}")
        except Exception:
            print("Could not get document_chunks count")

        try:
            new_docs_count = supabase.table('documents_new').select('count').execute()
            print(f"New documents count: {new_docs_count.data[0]['count']}")
        except Exception:
            print("Could not get documents_new count")

        # Test sample data
        try:
            sample = supabase.table('documents_new').select('*').limit(1).execute()
            if sample.data:
                print("\nSample document:")
                print(f"Content: {sample.data[0]['content'][:200]}...")
                print(f"Metadata: {sample.data[0]['metadata']}")
        except Exception as e:
            print("Could not fetch sample document")
            log_error(e, "Sample data fetch")

    except Exception as e:
        log_error(e, "Database connection test")
        raise

def test_vector_store():
    """Test vector store functionality."""
    try:
        print("\n2. Testing Vector Store...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        print("\nInitializing vector store...")
        vector_store = SupabaseVectorStore(
            embedding=embeddings,
            client=supabase,
            table_name="documents_new",
            query_name="match_documents"
        )

        # Test simple query
        print("\nTesting simple query...")
        test_query = "achoura"
        print(f"Query: '{test_query}'")

        # Test with different k values
        for k in [1, 3, 5]:
            print(f"\nTesting with k={k}...")
            results = vector_store.similarity_search(test_query, k=k)
            print(f"Found {len(results)} results")

            if results:
                print("\nSample results:")
                for i, doc in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"Content: {doc.page_content[:200]}...")
                    print(f"Metadata: {doc.metadata}")
            else:
                print("No results found!")

        return vector_store
    except Exception as e:
        log_error(e, "Vector store test")
        raise

def test_sql_function():
    """Test the match_documents SQL function directly."""
    try:
        print("\n3. Testing SQL Function Directly...")

        # Create a test embedding
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        test_query = "achoura"
        query_embedding = embeddings.embed_query(test_query)

        print(f"Testing query: '{test_query}'")

        # Call the function via RPC
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_count': 3
            }
        ).execute()

        print(f"\nFound {len(result.data)} results")

        if result.data:
            print("\nResults:")
            for i, row in enumerate(result.data, 1):
                print(f"\nResult {i}:")
                print(f"Content: {row['content'][:200]}...")
                print(f"Metadata: {row['metadata']}")
                print(f"Similarity: {row['similarity']}")
        else:
            print("No results found!")

    except Exception as e:
        log_error(e, "SQL function test")
        raise

def test_retriever():
    """Test the retriever functionality."""
    try:
        print("\n4. Testing Retriever...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        vector_store = SupabaseVectorStore(
            embedding=embeddings,
            client=supabase,
            table_name="documents_new",
            query_name="match_documents"
        )

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

        test_queries = [
            "achoura",
            "festival maroc",
            "tradition marocaine"
        ]

        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            results = retriever.get_relevant_documents(query)
            print(f"Found {len(results)} relevant documents")

            if results:
                print("\nResults:")
                for i, doc in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    print(f"Content: {doc.page_content[:200]}...")
                    print(f"Metadata: {doc.metadata}")
            else:
                print("No results found!")

    except Exception as e:
        log_error(e, "Retriever test")
        raise

if __name__ == "__main__":
    try:
        print("Starting RAG Debug Tests...")

        # Run all tests
        test_database_connection()
        test_vector_store()
        test_sql_function()
        test_retriever()

        print("\nAll tests completed!")

    except Exception as e:
        log_error(e, "Main execution")
        raise
