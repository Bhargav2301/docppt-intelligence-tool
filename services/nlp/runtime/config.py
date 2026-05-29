import os

# Options: 'gemini_byok'
MODEL_MODE = os.getenv("MODEL_MODE", "gemini_byok")

# Models configured from environment or defaults (from TRD)
SUMMARIZATION_MODEL = os.getenv("SUMMARIZATION_MODEL", "sshleifer/distilbart-cnn-12-6")
INSTRUCTION_MODEL = os.getenv("INSTRUCTION_MODEL", "google/flan-t5-small")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "distilgpt2")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
ADVANCED_INSTRUCTION_MODEL = os.getenv("ADVANCED_INSTRUCTION_MODEL", "llama3")
ADVANCED_MODEL_ENDPOINT = os.getenv("ADVANCED_MODEL_ENDPOINT", "http://localhost:11434/v1")

# Developer self-hosted / free managed endpoint configurations
MANAGED_LLM_ENDPOINT = os.getenv("MANAGED_LLM_ENDPOINT", "https://api.managed-llm.com/v1")
MANAGED_LLM_MODEL_NAME = os.getenv("MANAGED_LLM_MODEL_NAME", "llama3-70b")

# Cache path for HuggingFace Transformers
LOCAL_MODEL_CACHE_DIR = os.getenv("LOCAL_MODEL_CACHE_DIR", "/root/.cache/huggingface")

# Extractive configuration
EXTRACTIVE_SUMMARY_SENTENCE_COUNT = 3

# Evaluation Thresholds
HALLUCINATION_SIMILARITY_THRESHOLD = float(os.getenv("HALLUCINATION_SIMILARITY_THRESHOLD", "0.75"))

# Rewrite Constraints
REWRITE_MAX_EXPANSION = float(os.getenv("REWRITE_MAX_EXPANSION", "1.30"))
