-- 1. Create new documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS documents_new (
    id bigserial primary key,
    content text,
    metadata jsonb,
    embedding vector(1536)
);

-- 2. Migrate data from document_chunks to documents_new
INSERT INTO documents_new (content, metadata, embedding)
SELECT
    dc.chunk_text as content,
    jsonb_build_object(
        'filename', d.filename,
        'page', dc.metadata->>'page',
        'title', dc.metadata->>'title',
        'author', dc.metadata->>'author',
        'source', dc.metadata->>'source',
        'document_filename', dc.metadata->>'document_filename'
    ) as metadata,
    dc.embedding
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id;

-- 3. Drop existing function and create the new match_documents function
DROP FUNCTION IF EXISTS match_documents(vector, integer, jsonb);

CREATE OR REPLACE FUNCTION match_documents (
    query_embedding vector(1536),
    match_count int DEFAULT null,
    filter jsonb DEFAULT '{}'
) RETURNS TABLE (
    id bigint,
    content text,
    metadata jsonb,
    embedding jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
#variable_conflict use_column
BEGIN
    RETURN QUERY
    SELECT
        id,
        content,
        metadata,
        (embedding::text)::jsonb as embedding,
        1 - (documents_new.embedding <=> query_embedding) as similarity
    FROM documents_new
    WHERE metadata @> filter
    ORDER BY documents_new.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 4. Create index on the embedding column with reduced memory usage
SET maintenance_work_mem = '64MB';

CREATE INDEX IF NOT EXISTS documents_new_embedding_idx
ON documents_new
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

RESET maintenance_work_mem;

-- 5. Verify the migration
DO $$
BEGIN
    -- Check if we have data in the new table
    IF EXISTS (SELECT 1 FROM documents_new LIMIT 1) THEN
        RAISE NOTICE 'Migration successful! Data has been migrated to documents_new table.';

        -- Show counts
        RAISE NOTICE 'Old document_chunks count: %', (SELECT COUNT(*) FROM document_chunks);
        RAISE NOTICE 'New documents count: %', (SELECT COUNT(*) FROM documents_new);
    ELSE
        RAISE WARNING 'Migration might have failed - no data found in new table!';
    END IF;
END $$;

-- 6. Optional: Drop old tables if everything looks good
-- Uncomment these lines after verifying the migration
-- DROP TABLE IF EXISTS document_chunks;
-- DROP TABLE IF EXISTS documents;
-- ALTER TABLE documents_new RENAME TO documents;
