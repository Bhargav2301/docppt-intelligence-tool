CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    auth_provider TEXT DEFAULT 'email',
    google_linked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme TEXT DEFAULT 'dark',
    model_mode TEXT DEFAULT 'local_cpu',
    summarization_model TEXT,
    instruction_model TEXT,
    perplexity_model TEXT,
    embedding_model TEXT,
    ppt_sensitivity TEXT DEFAULT 'balanced',
    retain_source_files BOOLEAN DEFAULT true,
    auto_delete_days INTEGER,
    google_tokens_encrypted JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_type TEXT NOT NULL,
    input_type TEXT NOT NULL,
    input_label TEXT,
    input_url TEXT,
    status TEXT DEFAULT 'created',
    error_code TEXT,
    error_message TEXT,
    processing_started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_role TEXT NOT NULL,
    file_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    original_filename TEXT,
    mime_type TEXT,
    size_bytes BIGINT,
    checksum_sha256 TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE doc_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    source_title TEXT,
    source_word_count INTEGER,
    structured_summary TEXT NOT NULL,
    product_description TEXT NOT NULL,
    implementation_requirements JSONB NOT NULL,
    open_questions JSONB,
    assumptions JSONB,
    source_traceability JSONB,
    quality_report JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ppt_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    total_slides INTEGER NOT NULL,
    total_text_segments INTEGER DEFAULT 0,
    total_flags INTEGER DEFAULT 0,
    artifact_counts JSONB NOT NULL,
    accepted_rewrite_count INTEGER DEFAULT 0,
    rejected_rewrite_count INTEGER DEFAULT 0,
    export_file_id UUID REFERENCES files(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ppt_slide_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ppt_output_id UUID REFERENCES ppt_outputs(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    slide_index INTEGER NOT NULL,
    slide_number INTEGER NOT NULL,
    slide_title TEXT,
    flag_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending_review',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ppt_text_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ppt_slide_result_id UUID REFERENCES ppt_slide_results(id) ON DELETE CASCADE,
    shape_id TEXT,
    paragraph_index INTEGER,
    run_index INTEGER,
    segment_index INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    normalized_text TEXT,
    suggested_text TEXT,
    final_text TEXT,
    flags JSONB NOT NULL,
    quality_scores JSONB,
    semantic_similarity NUMERIC,
    decision TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE model_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    run_type TEXT NOT NULL,
    model_name TEXT,
    model_mode TEXT NOT NULL,
    input_tokens_estimate INTEGER,
    output_tokens_estimate INTEGER,
    duration_ms INTEGER,
    status TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_sessions_user_id_created_at ON sessions(user_id, created_at DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_files_session_id ON files(session_id);
CREATE INDEX idx_doc_outputs_session_id ON doc_outputs(session_id);
CREATE INDEX idx_ppt_outputs_session_id ON ppt_outputs(session_id);
CREATE INDEX idx_ppt_slide_results_output_id ON ppt_slide_results(ppt_output_id);
CREATE INDEX idx_ppt_text_segments_slide_id ON ppt_text_segments(ppt_slide_result_id);
CREATE INDEX idx_model_runs_session_id ON model_runs(session_id);

-- Seed Local User
INSERT INTO users (email, full_name, auth_provider) VALUES ('local_user@example.com', 'Local User', 'local');
