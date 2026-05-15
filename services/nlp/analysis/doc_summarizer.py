import logging
from runtime.registry import registry
from runtime.fallback import with_summarization_fallback

logger = logging.getLogger(__name__)

@with_summarization_fallback
def _generative_summarize(text: str) -> str:
    """Internal function wrapped with fallback logic to use Hugging Face summarization."""
    summarizer = registry.get_summarization_pipeline()
    if not summarizer:
        raise ValueError("Summarizer model not available, forcing fallback.")
    
    # Simple chunking to prevent max_length errors
    max_chunk_len = 1000
    chunks = [text[i:i+max_chunk_len] for i in range(0, len(text), max_chunk_len)]
    
    summaries = []
    for chunk in chunks[:5]: # limit to first 5 chunks for speed in MVP
        res = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
        summaries.append(res[0]['summary_text'])
        
    return " ".join(summaries)

def generate_structured_summary(text: str) -> str:
    """Generates the primary structured summary for the document."""
    if not text.strip():
        return "No text available for summary."
    return _generative_summarize(text)

def extract_product_description(text: str) -> str:
    """Extracts a high-level product description from the document."""
    # Heuristic: The product description is typically in the first few paragraphs.
    paragraphs = text.split('\n\n')
    intro_paragraphs = []
    word_count = 0
    for p in paragraphs:
        if not p.strip() or len(p) < 20:
            continue
        intro_paragraphs.append(p)
        word_count += len(p.split())
        if word_count > 150: # Roughly ~150 words is enough for a description
            break
    
    return "\n\n".join(intro_paragraphs)
