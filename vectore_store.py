import os
import uuid
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI, APIError # Use OpenAI v1+ library
from typing import List, Dict, Any, Optional, Tuple

# --- LangChain components for loading & splitting ---
# Use specific imports to avoid pulling in too much
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, WebBaseLoader, CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument # Alias to avoid naming conflict

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# --- Constants from environment or defaults ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Use service key for admin operations
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_EMBEDDING_DIMENSIONS = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", 1536))
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-3.5-turbo")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))

# --- Input Validation ---
if not all([OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    raise ValueError("Missing required environment variables (OpenAI key, Supabase URL/Key)")

# --- Initialize Clients ---
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logging.info("OpenAI and Supabase clients initialized.")
except Exception as e:
    logging.error(f"Failed to initialize clients: {e}")
    raise

# === Helper Functions ===

def _generate_uuid() -> uuid.UUID:
    """Generates a new UUID."""
    return uuid.uuid4()

def _get_openai_embedding(text: str, model: str = OPENAI_EMBEDDING_MODEL) -> Optional[List[float]]:
    """Generates embedding for a given text using OpenAI."""
    try:
        text = text.replace("\n", " ") # OpenAI recommends replacing newlines
        if not text: # Handle empty strings
             logging.warning("Attempted to embed empty string.")
             return None
        response = openai_client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except APIError as e:
        logging.error(f"OpenAI API error getting embedding: {e}")
    except Exception as e:
        logging.error(f"Unexpected error getting embedding for text '{text[:50]}...': {e}")
    return None

def _summarize_text(text: str, prompt_detail: str = "Provide a concise summary", model: str = OPENAI_CHAT_MODEL) -> Optional[str]:
    """Generates a summary for a given text using OpenAI Chat Completion."""
    if not text or not text.strip():
         logging.warning("Attempted to summarize empty or whitespace-only text.")
         return "N/A" # Or None, depending on how you want to handle this
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant skilled in summarizing text."},
                {"role": "user", "content": f"{prompt_detail} of the following text:\n\n{text}"}
            ],
            temperature=0.3, # Lower temperature for more factual summaries
            max_tokens=150 # Adjust as needed
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except APIError as e:
        logging.error(f"OpenAI API error during summarization: {e}")
    except Exception as e:
        logging.error(f"Unexpected error summarizing text '{text[:50]}...': {e}")
    return None


def _load_and_split_document(source: str, source_type: str = 'file') -> List[LangchainDocument]:
    """Loads and splits a document from file or URL."""
    loader = None
    documents = []
    try:
        if source_type == 'file':
            _, extension = os.path.splitext(source.lower())
            if extension == '.pdf':
                loader = PyPDFLoader(source)
            elif extension == '.txt':
                loader = TextLoader(source, encoding='utf-8') # Specify encoding
            elif extension == '.csv':
                loader = CSVLoader(source, encoding='utf-8')
            # Add other loaders as needed (e.g., UnstructuredFileLoader for docx, etc.)
            else:
                 raise ValueError(f"Unsupported file extension: {extension}")
        elif source_type == 'url':
            loader = WebBaseLoader(source)
        elif source_type == 'content': # Handle raw content string
             # Wrap content in Langchain Document for splitter compatibility
             documents = [LangchainDocument(page_content=source, metadata={"source": "raw_content"})]
        else:
             raise ValueError(f"Unsupported source_type: {source_type}")

        if loader:
            documents = loader.load()

        if not documents:
             logging.warning(f"No documents loaded from source: {source}")
             return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            add_start_index=True # Useful metadata for locating chunk origin
        )
        chunks = text_splitter.split_documents(documents)
        logging.info(f"Split source '{source}' into {len(chunks)} chunks.")
        return chunks

    except FileNotFoundError:
         logging.error(f"File not found: {source}")
         raise
    except Exception as e:
        logging.error(f"Failed to load/split document source '{source}': {e}")
        raise # Re-raise after logging

# === Core Vector Store Functions ===

def add_document(
    source: str,
    source_type: str = 'file', # 'file', 'url', or 'content'
    filename: Optional[str] = None, # Required if source_type is 'content' or for better identification
    doc_metadata: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Adds a document, splits it, generates summaries & embeddings, and stores everything in Supabase.

    Args:
        source (str): File path, URL, or raw text content.
        source_type (str): Type of the source ('file', 'url', 'content').
        filename (Optional[str]): Original filename or identifier (recommended).
        doc_metadata (Optional[Dict[str, Any]]): Optional metadata for the master document.

    Returns:
        Optional[str]: The UUID of the added master document, or None on failure.
    """
    if source_type == 'file' and not filename:
        filename = os.path.basename(source)
    elif not filename: # Assign a default name if none provided for url/content
        filename = f"source_{source_type}_{str(_generate_uuid())[:8]}"

    logging.info(f"Starting to add document: {filename} (Source: {source_type})")
    doc_id = _generate_uuid()
    doc_metadata = doc_metadata or {} # Ensure metadata is a dict

    try:
        # 1. Load and Split
        chunks = _load_and_split_document(source, source_type)
        if not chunks:
             logging.error(f"No processable chunks found for {filename}. Aborting add.")
             return None

        full_content = "\n\n".join([chunk.page_content for chunk in chunks]) # Reconstruct approx full content

        # 2. Generate Master Summary & Context (can be expensive)
        logging.info(f"Generating master summary for document {doc_id}...")
        master_summary = _summarize_text(full_content, "Provide a detailed overall summary") or "Summary generation failed."
        logging.info(f"Generating context/keywords for document {doc_id}...")
        master_context = _summarize_text(full_content, "Extract the main topics or keywords as a comma-separated list") or "Context generation failed."

        # 3. Store Master Document in 'documents' table
        logging.info(f"Inserting master document record {doc_id} into Supabase...")
        master_doc_data = {
            "id": str(doc_id),
            "filename": filename,
            "content": full_content, # Store full content
            "metadata": doc_metadata,
            "summary": master_summary,
            "context": master_context,
        }
        response = supabase.table("documents").insert(master_doc_data).execute()
        # Check response, Supabase client v2+ uses model_dump for data
        if not response.data:
            logging.error(f"Failed to insert master document {doc_id} into Supabase. Response: {response}")
            # Attempt cleanup or raise specific error based on response.error
            if hasattr(response, 'error') and response.error:
                 logging.error(f"Supabase error: {response.error.message}")
            raise Exception(f"Supabase insert failed for master document {doc_id}")

        logging.info(f"Master document {doc_id} inserted successfully.")

        # 4. Process and Store Chunks
        chunks_to_insert = []
        logging.info(f"Processing {len(chunks)} chunks for document {doc_id}...")
        for i, chunk in enumerate(chunks):
            logging.debug(f"Processing chunk {i+1}/{len(chunks)} for doc {doc_id}...")
            chunk_text = chunk.page_content

            # Generate chunk summary
            chunk_summary = _summarize_text(chunk_text, "Summarize this text chunk concisely") or "N/A"

            # Generate embedding
            embedding = _get_openai_embedding(chunk_text)
            if embedding is None:
                logging.warning(f"Skipping chunk {i+1} for doc {doc_id} due to embedding failure.")
                continue # Optionally handle this more robustly (e.g., retry, mark as failed)

            # Prepare chunk metadata (combine LangChain metadata with ours)
            chunk_meta = chunk.metadata.copy() # Start with LangChain's metadata
            chunk_meta["chunk_index"] = i # Add our own index
            # Add any other relevant chunk-level info here

            chunks_to_insert.append({
                # Let Supabase generate chunk UUID with default gen_random_uuid()
                "document_id": str(doc_id),
                "chunk_text": chunk_text,
                "chunk_summary": chunk_summary,
                "metadata": chunk_meta,
                "embedding": embedding,
            })

        # 5. Batch Insert Chunks
        if chunks_to_insert:
            logging.info(f"Batch inserting {len(chunks_to_insert)} chunks into Supabase for doc {doc_id}...")
            # Note: Supabase Python client might have limits on batch size.
            # For very large numbers of chunks, consider smaller batches.
            response = supabase.table("document_chunks").insert(chunks_to_insert).execute()
            if not response.data:
                logging.error(f"Failed to insert chunks for document {doc_id}. Response: {response}")
                # Consider rolling back the master document insert or marking it as incomplete
                if hasattr(response, 'error') and response.error:
                     logging.error(f"Supabase error during chunk insert: {response.error.message}")
                # Basic rollback attempt (might fail if chunks were partially inserted without transaction)
                # delete_document(str(doc_id)) # Be careful with cascading deletes
                raise Exception(f"Supabase insert failed for document chunks {doc_id}")
            logging.info(f"Successfully inserted {len(chunks_to_insert)} chunks for document {doc_id}.")
        else:
             logging.warning(f"No valid chunks generated embeddings for document {doc_id}. Document added but may be unusable.")

        logging.info(f"Document '{filename}' (ID: {doc_id}) added successfully.")
        return str(doc_id)

    except Exception as e:
        logging.exception(f"Error adding document '{filename}': {e}")
        # Attempt cleanup: If doc_id was generated and possibly inserted, try deleting.
        # This is basic; real transactions would be better if Supabase client supports them easily.
        # if 'doc_id' in locals() and doc_id:
        #    try:
        #       logging.warning(f"Attempting cleanup for failed add operation (doc_id: {doc_id})...")
        #       delete_document(str(doc_id))
        #    except Exception as cleanup_e:
        #       logging.error(f"Cleanup failed for doc_id {doc_id}: {cleanup_e}")
        return None


def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a master document and its associated chunks from Supabase."""
    logging.info(f"Retrieving document with ID: {document_id}")
    try:
        # Get master document
        response_doc = supabase.table("documents").select("*").eq("id", document_id).maybe_single().execute()
        if not response_doc.data:
            logging.warning(f"Document with ID {document_id} not found.")
            return None
        master_document = response_doc.data

        # Get associated chunks (without embeddings to save bandwidth unless needed)
        response_chunks = supabase.table("document_chunks").select(
            "id, document_id, chunk_text, chunk_summary, metadata, created_at" # Exclude embedding
        ).eq("document_id", document_id).order("metadata->>chunk_index").execute() # Order by chunk index if available

        master_document["chunks"] = response_chunks.data if response_chunks.data else []
        logging.info(f"Found document {document_id} with {len(master_document['chunks'])} chunks.")
        return master_document

    except Exception as e:
        logging.exception(f"Error retrieving document {document_id}: {e}")
        return None


def query_with_llm(
    query_text: str,
    top_k: int = 5,
    match_threshold: float = 0.75,
    rerank: bool = False # Placeholder for future reranking logic
    ) -> Optional[str]:
    """
    Queries the vector store, retrieves chunks, and uses an LLM to generate an answer.
    """
    logging.info(f"Starting LLM query for: '{query_text[:50]}...'")
    try:
        # 1. Retrieve relevant chunks
        relevant_chunks = query_vector_store(query_text, top_k, match_threshold)

        if not relevant_chunks:
            logging.warning("No relevant context found in vector store for the query.")
            # Optionally, still ask the LLM but without specific context
            # return _ask_llm_without_context(query_text)
            return "I couldn't find specific information in the documents to answer your question."

        # Optional: Reranking step could happen here using a more sophisticated model if needed

        # 2. Format Context for LLM
        # Combine chunk text and potentially summaries for context
        context_parts = []
        for i, chunk in enumerate(relevant_chunks):
            context_parts.append(f"Source Chunk {i+1} (Similarity: {chunk.get('similarity', 'N/A'):.4f}):\n{chunk.get('chunk_text', '')}")
            # Optionally add chunk summaries:
            # if chunk.get('chunk_summary'):
            #    context_parts.append(f"Chunk {i+1} Summary: {chunk['chunk_summary']}")
        context_str = "\n\n---\n\n".join(context_parts)

        # 3. Prepare Prompt and Query LLM
        system_prompt = "You are an AI assistant. Answer the user's question based *only* on the provided context. If the context doesn't contain the answer, say so clearly. Do not use prior knowledge."
        user_prompt = f"Context:\n{context_str}\n\n---\n\nQuestion: {query_text}\n\nAnswer:"

        logging.info(f"Querying LLM ({OPENAI_CHAT_MODEL}) with retrieved context...")
        response = openai_client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2, # Lower temperature for fact-based Q&A
        )

        llm_answer = response.choices[0].message.content.strip()
        logging.info("LLM query completed.")
        return llm_answer

    except APIError as e:
        logging.error(f"OpenAI API error during LLM query phase: {e}")
        return "An error occurred while contacting the AI model."
    except Exception as e:
        logging.exception(f"Error during LLM query processing: {e}")
        return "An unexpected error occurred while processing your query."
