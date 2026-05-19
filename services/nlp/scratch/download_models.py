import os
import sys

# Add parent directories to sys.path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.config import SUMMARIZATION_MODEL, INSTRUCTION_MODEL, PERPLEXITY_MODEL, EMBEDDING_MODEL

def download_all():
    print("Initializing model pre-downloads for local-first execution...")
    
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Required libraries (transformers, sentence_transformers, torch) are not installed.")
        print("Please run `pip install -r requirements.txt` first.")
        sys.exit(1)

    print(f"1. Downloading Summarization Model: {SUMMARIZATION_MODEL}...")
    pipeline("summarization", model=SUMMARIZATION_MODEL)
    print("Summarization model downloaded successfully!")

    print(f"2. Downloading Instruction/Rewrite Model: {INSTRUCTION_MODEL}...")
    pipeline("text2text-generation", model=INSTRUCTION_MODEL)
    print("Instruction model downloaded successfully!")

    print(f"3. Downloading Perplexity Model: {PERPLEXITY_MODEL}...")
    AutoTokenizer.from_pretrained(PERPLEXITY_MODEL)
    AutoModelForCausalLM.from_pretrained(PERPLEXITY_MODEL)
    print("Perplexity model downloaded successfully!")

    print(f"4. Downloading Embedding Model: {EMBEDDING_MODEL}...")
    SentenceTransformer(EMBEDDING_MODEL)
    print("Embedding model downloaded successfully!")

    print("\nAll default models downloaded and cached successfully!")

if __name__ == "__main__":
    download_all()
