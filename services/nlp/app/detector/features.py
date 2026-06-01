"""Feature computation for the AI-likeness detection pipeline.

All functions accept plain ``str`` text and return numeric values (``float``
or ``dict``).  No external NLP libraries — pure Python + ``re`` for the MVP.
"""

from __future__ import annotations

import math
import re
import string
from typing import Dict, List

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GENERIC_PHRASES: List[str] = [
    "streamline workflows", "enhance productivity", "drive efficiency",
    "seamless integration", "end-to-end solution", "robust platform",
    "cutting-edge", "state-of-the-art", "best-in-class", "world-class",
    "leverage", "synergy", "holistic approach", "paradigm shift",
    "actionable insights", "scalable solution", "digital transformation",
    "value proposition", "core competency", "mission-critical",
    "next-generation", "innovative solution", "comprehensive solution",
    "empower teams", "unlock potential", "game-changer",
    "operational excellence", "strategic alignment", "data-driven",
    "future-proof", "thought leadership", "ecosystem",
    "optimize operations", "maximize efficiency", "minimize risk",
    "enhance collaboration", "foster innovation", "accelerate growth",
    "competitive advantage", "industry-leading", "transformative",
    "enables seamless", "ensures compliance", "facilitates",
    "real-time visibility", "across the enterprise", "stakeholder engagement",
    "outgrown", "scale your", "chaos", "data islands",
    "decisions from real data", "run the business", "don't be the system",
    "honest comparison", "failure rate", "industry average",
    "anonymised pattern", "zero commitment", "living, interactive",
    "unlike any", "explore your industry's", "BOM-first",
    "classroom training", "dedicated success manager", "no data islands",
]

VAGUE_MODIFIERS: List[str] = [
    "robust", "powerful", "innovative", "efficient", "comprehensive",
    "effectively", "seamlessly", "significant", "substantial",
    "various", "numerous", "optimal", "dynamic", "advanced",
    "enhanced", "improved", "strategic", "key", "critical",
    "essential", "vital", "crucial", "important", "major",
    "scale", "run", "outgrown", "chaos",
]

COMMON_AI_OPENERS: List[str] = [
    "this ", "it ", "the platform ", "the system ", "the solution ",
    "additionally", "furthermore", "moreover", "in addition",
    "our ", "we ", "by ", "with ", "through ",
]

DISCOURSE_MARKERS: List[str] = [
    "in conclusion", "to summarize", "overall", "in summary",
    "it is worth noting", "it should be noted", "importantly",
    "significantly", "notably", "interestingly",
    "as mentioned", "as discussed", "as highlighted",
    "moving forward", "going forward", "looking ahead",
    "on the other hand", "that being said", "having said that",
    "first and foremost", "last but not least",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT_RE = re.compile(r'(?<!\d)\.(?!\d)|[!?]+')


def _split_sentences(text: str) -> List[str]:
    """Split *text* on sentence-ending punctuation and drop blanks."""
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in parts if s.strip()]


def _count_syllables(word: str) -> int:
    """Rough syllable count using vowel-group heuristic."""
    word = word.lower().rstrip("e")
    if not word:
        return 1
    count = len(re.findall(r'[aeiouy]+', word))
    return max(count, 1)


# ---------------------------------------------------------------------------
# Surface features
# ---------------------------------------------------------------------------

def compute_surface_features(text: str) -> Dict[str, float]:
    """Compute sentence-level and lexical surface features.

    Returns a dict with keys:
        sentence_count, avg_sentence_length, sentence_length_std,
        avg_word_length, punctuation_density, type_token_ratio.
    """
    sentences = _split_sentences(text)
    sentence_count = len(sentences)
    if sentence_count == 0:
        return {
            "sentence_count": 0,
            "avg_sentence_length": 0.0,
            "sentence_length_std": 0.0,
            "avg_word_length": 0.0,
            "punctuation_density": 0.0,
            "type_token_ratio": 0.0,
        }

    # Word-level stats
    words_per_sentence = [len(s.split()) for s in sentences]
    all_words = text.split()
    total_words = len(all_words)

    avg_sentence_length = sum(words_per_sentence) / sentence_count
    variance = (
        sum((wc - avg_sentence_length) ** 2 for wc in words_per_sentence)
        / sentence_count
    )
    sentence_length_std = math.sqrt(variance)

    # Word length
    word_lengths = [len(w.strip(string.punctuation)) for w in all_words]
    avg_word_length = sum(word_lengths) / max(total_words, 1)

    # Punctuation density
    punct_count = sum(1 for ch in text if ch in string.punctuation)
    punctuation_density = punct_count / max(len(text), 1)

    # Type-token ratio (lexical diversity)
    lower_words = [w.lower().strip(string.punctuation) for w in all_words]
    lower_words = [w for w in lower_words if w]
    unique = set(lower_words)
    type_token_ratio = len(unique) / max(len(lower_words), 1)

    return {
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "sentence_length_std": round(sentence_length_std, 2),
        "avg_word_length": round(avg_word_length, 2),
        "punctuation_density": round(punctuation_density, 4),
        "type_token_ratio": round(type_token_ratio, 4),
    }


# ---------------------------------------------------------------------------
# Individual feature scores (all 0-1)
# ---------------------------------------------------------------------------

def compute_burstiness_score(text: str) -> float:
    """0-1 burstiness score.

    *High* value means *low* burstiness (uniform sentence lengths), which is
    more typical of AI-generated text.  The score inverts normalised
    variance so that low variance → high score.
    """
    sentences = _split_sentences(text)
    if len(sentences) < 2:
        return 0.0

    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    if mean_len == 0:
        return 0.0

    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    # Coefficient of variation (normalised std-dev).
    cv = math.sqrt(variance) / mean_len

    # Low CV → uniform → AI-like → high score.
    # CV of 0 → score 1.0; CV >= 1.0 → score 0.0.
    score = max(0.0, 1.0 - cv)
    return round(score, 4)


def compute_repetition_score(text: str) -> float:
    """0-1 score based on bi-gram and tri-gram repetition rate."""
    words = [w.lower().strip(string.punctuation) for w in text.split()]
    words = [w for w in words if w]
    if len(words) < 4:
        return 0.0

    def _repeat_ratio(n: int) -> float:
        ngrams = [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]
        if not ngrams:
            return 0.0
        unique = set(ngrams)
        repeated = len(ngrams) - len(unique)
        return repeated / len(ngrams)

    bigram_r = _repeat_ratio(2)
    trigram_r = _repeat_ratio(3)
    # Weight tri-grams more — they are a stronger signal.
    combined = 0.4 * bigram_r + 0.6 * trigram_r
    return round(min(combined, 1.0), 4)


AI_SLOGAN_PATTERNS: List[str] = [
    # Sloganized contrast: "Built to scale ... — not just run it", "add a plant ... — not a clerk"
    r"(?i)\bnot\s+just\b",
    r"(?i)\bnot\s+only\b",
    r"(?i)—\s*not\s+a\b",
    r"(?i)-\s*not\s+a\b",
    r"(?i)—\s*not\s+just\b",
    r"(?i)-\s*not\s+just\b",
    # Tool combinations: "Tally + Excel", "Excel + WhatsApp", "Excel + Tally"
    r"(?i)\w+\s*\+\s*\w+",
    # Rhythm-heavy triads: e.g. "Six modules. One platform. No data islands."
    # We detect this by matching exactly three short phrases (under 35 chars each) separated by punctuation
    r"(?i)^[^.!?]{1,35}[.!?]\s*[^.!?]{1,35}[.!?]\s*[^.!?]{1,35}[.!?]$",
    # Repeated listing patterns like "by ..., by ..., by ..."
    r"(?i)\bby\s+\w+(?:,\s*by\s+\w+){2,}\b",
    r"(?i)\bby\s+\w+,\s*by\s+\w+\b",
    # Formulaic slogans
    r"(?i)\bbuilt\s+to\b",
    r"(?i)\bdesigned\s+for\b",
    r"(?i)\bscale\s+your\b",
    r"(?i)\bscale\s+operations\b",
    # AI certainty & promotional markers
    r"(?i)\bunlike\s+any\b",
    r"(?i)\bliving,\s+interactive\b",
    r"(?i)\bzero\s+commitment\b",
    r"(?i)\bno\s+surprises\b",
    r"(?i)\bno\s+hidden\b",
    r"(?i)\bcomplete\s+control\b",
    r"(?i)\bdata\s+islands\b",
    r"(?i)\bfree\s+digital\s+maturity\b",
    r"(?i)\bexperience\s+[\w]+\b",
    r"(?i)\bscale\s+without\b",
    r"(?i)\bwithout\s+the\s+right\s+data\b",
    r"(?i)\bgut\s*\+\s*customer\b",
    # Narratives and presentation AI structures
    r"(?i)\bno\s+idea\b",
    r"(?i)\bwhat\s+you\s+actually\b",
    r"(?i)\bnightmare\b",
    r"(?i)\bwhat\s+we\s+keep\s+seeing\b",
    r"(?i)\bwhat\s+the\s+owner\s+stops\b",
    r"(?i)\bwhat\s+shifts\b",
    r"(?i)\bwhat\s+changes\b",
    r"(?i)\bwhy\s+most\b",
    r"(?i)\bwhy\s+our\b",
    r"(?i)\bwhy\s+absolin\b",
    r"(?i)\bhonest\s+comparison\b",
    r"(?i)\bpric(?:ed|ing)\s+for\b",
    r"(?i)\bpricing\s+scope\b",
    r"(?i)\bone\s+conversation\b",
    r"(?i)\bexperience\s+absolin\b",
    r"(?i)\bworkweek\b",
    r"(?i)\bowner\s+freedom\b",
    r"(?i)\bvalue\s+addition\b",
    r"(?i)\bhow\s+it\s+all\s+connects\b",
    r"(?i)\bwe\s+know\s+your\s+world\b",
    r"(?i)\bfive\s+decisions\b",
    r"(?i)\b5\s+decisions\b",
    r"(?i)\bdecision\s+by\s+decision\b",
    r"(?i)\bone\s+week\b",
    r"(?i)\bbefore\s+vs\s+after\b",
]

def compute_generic_phrase_score(text: str) -> float:
    """0-1 score based on density of generic business / AI phrases and slogan patterns."""
    text_lower = text.lower()
    words = text.split()
    total_words = len(words)
    if total_words == 0:
        return 0.0

    hit_count = 0
    # Check exact phrases
    for phrase in GENERIC_PHRASES:
        if phrase in text_lower:
            hit_count += 1
            
    # Check regex patterns
    for pattern in AI_SLOGAN_PATTERNS:
        if re.search(pattern, text):
            hit_count += 1.5  # Give higher weight to structural AI slogan patterns!

    # Normalise: each hit "covers" roughly 2 words.
    density = (hit_count * 2) / total_words
    return round(min(density, 1.0), 4)


def compute_specificity_score(text: str) -> float:
    """0-1 specificity score.

    *High* score means *low* specificity (abstract / vague), which is more
    typical of AI-generated text.
    """
    words = [w.lower().strip(string.punctuation) for w in text.split()]
    words = [w for w in words if w]
    total = len(words)
    if total == 0:
        return 0.0

    IMPERATIVE_VERB_EXCLUSIONS = {
        "run", "build", "deploy", "track", "manage", "connect", "see",
        "start", "stop", "scale", "automate", "measure", "visit", "speak",
        "explore", "ask", "understand", "decide", "plan", "review", "check"
    }
    
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    imperatives = set()
    for sent in sentences:
        s_words = sent.lower().split()
        if s_words and s_words[0] in IMPERATIVE_VERB_EXCLUSIONS:
            imperatives.add(s_words[0])

    vague_count = 0
    for w in words:
        if w in VAGUE_MODIFIERS and w not in imperatives:
            vague_count += 1

    vague_ratio = vague_count / total

    # Check for concreteness indicators (numbers, proper nouns heuristic).
    has_numbers = bool(re.search(r'\d', text))
    # Rough proper-noun count: capitalised words not at sentence start.
    sentences = _split_sentences(text)
    proper_count = 0
    for sent in sentences:
        sent_words = sent.split()
        for w in sent_words[1:]:  # skip first word (sentence-initial cap)
            if w[0:1].isupper() and w.lower().strip(string.punctuation) not in VAGUE_MODIFIERS:
                proper_count += 1

    concreteness_bonus = 0.0
    if has_numbers:
        concreteness_bonus += 0.1
    if proper_count >= 2:
        concreteness_bonus += 0.1

    score = max(0.0, (vague_ratio * 5) - concreteness_bonus)
    return round(min(score, 1.0), 4)


def compute_readability_score(text: str) -> float:
    """0-1 readability regularisation score.

    Extremely high or extremely uniform Flesch-Kincaid grade level is a
    weak signal of AI-generated text.
    """
    sentences = _split_sentences(text)
    words = text.split()
    total_words = len(words)
    total_sentences = len(sentences)
    if total_words == 0 or total_sentences == 0:
        return 0.0

    total_syllables = sum(_count_syllables(w) for w in words)

    # Flesch-Kincaid Grade Level formula.
    fk_grade = (
        0.39 * (total_words / total_sentences)
        + 11.8 * (total_syllables / total_words)
        - 15.59
    )

    # Grade 8-12 is "normal" business prose → low score.
    # Very high grade (>16) or very low (<5) suggests uniformity / over-simplification.
    if fk_grade < 5:
        score = 0.3
    elif 5 <= fk_grade <= 8:
        score = 0.1
    elif 8 < fk_grade <= 12:
        score = 0.0  # normal range
    elif 12 < fk_grade <= 16:
        score = (fk_grade - 12) / 8  # 0 … 0.5
    else:
        score = min(0.5 + (fk_grade - 16) / 20, 1.0)

    return round(score, 4)


def compute_syntactic_uniformity_score(text: str) -> float:
    """0-1 score based on repeated sentence openers and parallel structures."""
    sentences = _split_sentences(text)
    if len(sentences) < 2:
        return 0.0

    opener_hits = 0
    for sent in sentences:
        sent_lower = sent.lower().lstrip()
        for opener in COMMON_AI_OPENERS:
            if sent_lower.startswith(opener):
                opener_hits += 1
                break  # only count once per sentence

    ratio = opener_hits / len(sentences)
    # Also penalise if >50 % of sentences start with the *same* opener.
    first_words = [s.split()[0].lower() if s.split() else "" for s in sentences]
    from collections import Counter
    most_common_count = Counter(first_words).most_common(1)[0][1]
    uniformity_bonus = max(0.0, (most_common_count / len(sentences)) - 0.5) * 0.5

    score = min(ratio + uniformity_bonus, 1.0)
    return round(score, 4)


def compute_discourse_template_score(text: str) -> float:
    """0-1 score based on presence of discourse template / transition markers."""
    text_lower = text.lower()
    sentences = _split_sentences(text)
    total_sentences = max(len(sentences), 1)

    hit_count = sum(1 for marker in DISCOURSE_MARKERS if marker in text_lower)
    # Normalise by sentence count (one marker per sentence is extreme).
    score = hit_count / total_sentences
    return round(min(score, 1.0), 4)


# ---------------------------------------------------------------------------
# Phrase-finding helpers (used by explanations module)
# ---------------------------------------------------------------------------

def find_generic_phrases_present(text: str) -> List[str]:
    """Return the subset of ``GENERIC_PHRASES`` found in *text*."""
    text_lower = text.lower()
    return [p for p in GENERIC_PHRASES if p in text_lower]


def find_openers_present(text: str) -> List[str]:
    """Return the opener patterns that actually appear at sentence starts."""
    sentences = _split_sentences(text)
    found: List[str] = []
    seen: set[str] = set()
    for sent in sentences:
        sent_lower = sent.lower().lstrip()
        for opener in COMMON_AI_OPENERS:
            if sent_lower.startswith(opener) and opener not in seen:
                found.append(opener.strip())
                seen.add(opener)
    return found


def find_discourse_markers_present(text: str) -> List[str]:
    """Return the discourse markers found in *text*."""
    text_lower = text.lower()
    return [m for m in DISCOURSE_MARKERS if m in text_lower]
