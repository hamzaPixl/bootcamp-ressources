# import basics
import os
from dotenv import load_dotenv
import json
from typing import List, Dict
from uuid import uuid4
from datetime import datetime

# import langchain
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# import supabase
from supabase.client import Client, create_client
import traceback
from tqdm import tqdm

# load environment variables
load_dotenv()

def log_message(message: str):
    """Print a formatted log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def log_error(e: Exception, context: str):
    """Log error with context and stack trace."""
    print(f"\n❌ Error in {context}:")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    print("\nStack trace:")
    print(traceback.format_exc())

def initialize_connections():
    """Initialize database and model connections with error handling."""
    try:
        # Check environment variables
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_KEY"):
            raise ValueError("Missing Supabase credentials in .env file")
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("Missing OpenAI API key in .env file")

        # Initialize Supabase
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(supabase_url, supabase_key)

        # Initialize models
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        llm = ChatOpenAI(model="gpt-3.5-turbo")

        return supabase, embeddings, llm
    except Exception as e:
        log_error(e, "Failed to initialize connections")
        raise

def generate_summary(text: str, llm: ChatOpenAI) -> str:
    """Generate a summary of the document using LLM."""
    try:
        prompt = f"Please provide a concise summary of the following text:\n\n{text[:2000]}"
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        log_error(e, "Failed to generate summary")
        return "Summary generation failed"

def extract_context(text: str, llm: ChatOpenAI) -> str:
    """Extract key context/keywords from the document."""
    try:
        prompt = f"Extract key topics, themes, and important keywords from this text:\n\n{text[:2000]}"
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        log_error(e, "Failed to extract context")
        return "Context extraction failed"

def process_document(doc: Dict, llm: ChatOpenAI) -> Dict:
    """Process a single document and prepare it for database insertion."""
    try:
        doc_id = str(uuid4())
        filename = os.path.basename(doc.metadata.get("source", ""))

        log_message(f"Processing document: {filename}")

        # Generate document-level metadata
        log_message(f"Generating summary for {filename}")
        summary = generate_summary(doc.page_content, llm)

        log_message(f"Extracting context for {filename}")
        context = extract_context(doc.page_content, llm)

        # Prepare document metadata
        metadata = {
            "source": doc.metadata.get("source", ""),
            "page": doc.metadata.get("page", 0),
            "file_path": doc.metadata.get("file_path", "")
        }

        return {
            "id": doc_id,
            "filename": filename,
            "content": doc.page_content,
            "metadata": metadata,
            "summary": summary,
            "context": context
        }
    except Exception as e:
        log_error(e, f"Failed to process document {doc.metadata.get('source', 'unknown')}")
        raise

def process_chunks(doc_id: str, chunks: List[Dict], llm: ChatOpenAI) -> List[Dict]:
    """Process document chunks and prepare them for database insertion."""
    try:
        processed_chunks = []
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks, 1):
            try:
                chunk_id = str(uuid4())
                log_message(f"Processing chunk {i}/{total_chunks} for document {doc_id}")

                chunk_summary = generate_summary(chunk.page_content, llm)

                processed_chunks.append({
                    "id": chunk_id,
                    "document_id": doc_id,
                    "chunk_text": chunk.page_content,
                    "chunk_summary": chunk_summary,
                    "metadata": chunk.metadata
                })
            except Exception as e:
                log_error(e, f"Failed to process chunk {i} for document {doc_id}")
                continue

        return processed_chunks
    except Exception as e:
        log_error(e, f"Failed to process chunks for document {doc_id}")
        raise

def process_pdf(file_path: str):
    """Process a single PDF file and return its chunks."""
    try:
        loader = PyPDFDirectoryLoader(file_path)
        pages = loader.load()

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        chunks = text_splitter.split_documents(pages)
        return chunks

    except Exception as e:
        log_error(e, f"Processing PDF: {file_path}")
        return []

def ingest_documents():
    """Ingest documents into the database."""
    try:
        print("Starting document ingestion...")

        # Initialize connections
        supabase, embeddings, llm = initialize_connections()

        # Get all PDF files
        pdf_dir = "documents"
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

        if not pdf_files:
            print("No PDF files found in documents directory!")
            return

        print(f"Found {len(pdf_files)} PDF files to process")

        # Process each PDF
        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            file_path = os.path.join(pdf_dir, pdf_file)
            chunks = process_pdf(file_path)

            if not chunks:
                print(f"Skipping {pdf_file} - no valid chunks found")
                continue

            print(f"\nProcessing {pdf_file} - {len(chunks)} chunks")

            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]

                # Prepare documents for insertion
                documents = []
                for chunk in batch:
                    # Generate embedding
                    embedding = embeddings.embed_query(chunk.page_content)

                    # Prepare document
                    doc = {
                        'content': chunk.page_content,
                        'metadata': {
                            'filename': pdf_file,
                            'page': chunk.metadata.get('page', 0),
                            'source': chunk.metadata.get('source', ''),
                        },
                        'embedding': embedding
                    }
                    documents.append(doc)

                # Insert batch
                try:
                    result = supabase.table('documents_new').insert(documents).execute()
                    print(f"Inserted batch {i//batch_size + 1} of {len(chunks)//batch_size + 1}")
                except Exception as e:
                    log_error(e, f"Inserting batch for {pdf_file}")
                    continue

        print("\nDocument ingestion completed!")

    except Exception as e:
        log_error(e, "Document ingestion")
        raise

if __name__ == "__main__":
    try:
        ingest_documents()
    except Exception as e:
        log_error(e, "Main execution")
        raise
