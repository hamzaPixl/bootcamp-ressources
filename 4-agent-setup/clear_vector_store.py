import os
import shutil
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_vector_stores():
    """Clear all vector stores by removing their directories"""
    vector_stores = ['conversation_store', 'knowledge_store']

    for store in vector_stores:
        if os.path.exists(store):
            logger.info(f"Removing vector store: {store}")
            shutil.rmtree(store)
            logger.info(f"Successfully removed {store}")
        else:
            logger.info(f"Vector store {store} does not exist, skipping")

    logger.info("All vector stores cleared")

if __name__ == "__main__":
    load_dotenv()
    clear_vector_stores()
    logger.info("Vector stores cleanup complete. The application will start with fresh stores on next run.")
