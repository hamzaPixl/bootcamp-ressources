import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from utils.logger import logger

def initialize_embedding_model():
    """Initialize and return the OpenAI embeddings model."""
    logger.info("Initializing embedding model")
    return OpenAIEmbeddings()

def initialize_vector_store(embedding_model, persist_directory="vector_store", collection_name="documents"):
    """Initialize vector store for conversation tracking"""
    # Create a shared directory for all collections
    os.makedirs(persist_directory, exist_ok=True)

    # Initialize conversation store for tracking conversation history
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_directory
    )
    logger.info(f"🗃️ Initialized vector store: {collection_name}")
    return vector_store

def save_document_to_store(vector_store, content, metadata):
    """Save a document to the vector store with the given content and metadata."""
    try:
        vector_store.add_documents([
            Document(page_content=content, metadata=metadata)
        ])
        logger.info(f"✅ Document saved successfully to vector store")
        return True
    except Exception as e:
        logger.error(f"Error saving document to vector store: {str(e)}")
        return False

def get_documents_from_store(vector_store, where_filter=None):
    """Retrieve documents from the vector store based on a filter."""
    try:
        results = vector_store.get(where=where_filter)
        return results
    except Exception as e:
        logger.error(f"Error retrieving documents from vector store: {str(e)}")
        return None
