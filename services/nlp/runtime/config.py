import os

# Options: 'local_cpu', 'local_gpu', 'extractive_only', 'user_hosted_endpoint'
MODEL_MODE = os.getenv("MODEL_MODE", "extractive_only")

# Models configured from environment or defaults (from TRD)
SUMMARIZATION_MODEL = os.getenv("SUMMARIZATION_MODEL", "sshleifer/distilbart-cnn-12-6")
INSTRUCTION_MODEL = os.getenv("INSTRUCTION_MODEL", "google/flan-t5-small")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "distilgpt2")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Cache path for HuggingFace Transformers
LOCAL_MODEL_CACHE_DIR = os.getenv("LOCAL_MODEL_CACHE_DIR", "/root/.cache/huggingface")

# Extractive configuration
EXTRACTIVE_SUMMARY_SENTENCE_COUNT = 3

# Evaluation Thresholds
HALLUCINATION_SIMILARITY_THRESHOLD = float(os.getenv("HALLUCINATION_SIMILARITY_THRESHOLD", "0.75"))
