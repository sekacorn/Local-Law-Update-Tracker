-- Migration 003: User Uploads Support
-- Adds support for user-uploaded documents, version metadata, and pinned documents

-- Add user upload fields to document table
ALTER TABLE document ADD COLUMN is_user_uploaded INTEGER DEFAULT 0;
ALTER TABLE document ADD COLUMN original_filename TEXT;
ALTER TABLE document ADD COLUMN upload_mime TEXT;
ALTER TABLE document ADD COLUMN source_path TEXT;

-- Add version metadata fields
ALTER TABLE version ADD COLUMN parse_warnings_json TEXT;
ALTER TABLE version ADD COLUMN page_map_json TEXT;

-- Create pinned_document table
CREATE TABLE IF NOT EXISTS pinned_document (
    document_id TEXT PRIMARY KEY,
    pinned_ts TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES document(doc_id) ON DELETE CASCADE
);

-- Create index for faster pinned document lookups
CREATE INDEX IF NOT EXISTS idx_pinned_document_ts ON pinned_document(pinned_ts DESC);

-- Create index for user uploads
CREATE INDEX IF NOT EXISTS idx_document_user_uploaded ON document(is_user_uploaded) WHERE is_user_uploaded = 1;

-- Create index for upload mime types
CREATE INDEX IF NOT EXISTS idx_document_upload_mime ON document(upload_mime) WHERE upload_mime IS NOT NULL;
