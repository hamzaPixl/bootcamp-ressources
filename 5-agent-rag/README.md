# RAG Agent with PDF Documents

A Retrieval-Augmented Generation (RAG) system that allows you to query PDF documents using natural language. The system uses Supabase for vector storage and OpenAI for embeddings and language models.

## Features

- PDF document ingestion and chunking
- Vector embeddings for semantic search
- Natural language querying
- Source citation in responses
- Interactive query interface

## Prerequisites

- Python 3.8+
- Supabase account
- OpenAI API key

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your credentials:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
OPENAI_API_KEY=your_openai_api_key
```

3. Set up the database:

```bash
psql -U your_user -d your_db -f supabase_setup.sql
```

4. Place your PDF documents in the `documents` directory

## Usage

### 1. Ingest Documents

Run the ingestion script to process and store your PDFs:

```bash
python ingest_in_db.py
```

This will:

- Load PDFs from the `documents` directory
- Split them into chunks
- Generate embeddings
- Store them in Supabase

### 2. Query Documents

Start the interactive query interface:

```bash
python agentic_rag.py
```

Example queries:

- "What is Soltan Tolba?"
- "Tell me about Moroccan traditions"
- "Explain the history of Casablanca"

### 3. Debug and Verify

Run the debug script to verify the setup:

```bash
python debug_rag.py
```

This will:

- Test database connection
- Verify vector store functionality
- Test the SQL function
- Check retriever performance

## System Architecture

### Database Structure

The system uses two main tables:

1. `documents_new`: Stores document chunks with embeddings
   - `id`: Unique identifier
   - `content`: Text content
   - `metadata`: JSON containing filename, page, etc.
   - `embedding`: Vector embedding of the content

### Components

1. **Document Processing**

   - PDF loading and chunking
   - Text splitting with overlap
   - Embedding generation

2. **Vector Store**

   - Supabase integration
   - Similarity search
   - Metadata filtering

3. **Query Interface**
   - Natural language processing
   - Document retrieval
   - Response generation

## Troubleshooting

Common issues and solutions:

1. **Memory Errors**

   - Reduce batch size in `ingest_in_db.py`
   - Adjust `maintenance_work_mem` in Supabase

2. **No Results Found**

   - Check document ingestion
   - Verify vector store configuration
   - Test with debug script

3. **Connection Issues**
   - Verify environment variables
   - Check Supabase credentials
   - Test database connection

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License
