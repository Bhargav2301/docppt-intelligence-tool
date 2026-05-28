"""Editorial rules enforcement for the DocPPT Intelligence Tool.

Applies American English spelling normalization, punctuation/grammar fixes,
and emoji removal to all text before export or display.

Usage::

    >>> from app.humanizer.editorial_rules import apply_all_editorial_rules
    >>> apply_all_editorial_rules("Optimise the colour scheme 🎨")
    'Optimize the color scheme.'
"""

from __future__ import annotations

import re
import unicodedata
from typing import Tuple

# ---------------------------------------------------------------------------
# British → American spelling dictionary (~200 entries)
# ---------------------------------------------------------------------------
# Patterns covered:
#   -ise  → -ize   (optimise→optimize, recognise→recognize, …)
#   -our  → -or    (colour→color, behaviour→behavior, …)
#   -re   → -er    (centre→center, metre→meter, …)
#   -ence → -ense  (defence→defense, offence→offense, …)
#   -yse  → -yze   (analyse→analyze, paralyse→paralyze, …)
#   -ogue → -og    (catalogue→catalog, dialogue→dialog, …)
#   -lled → -led   (modelled→modeled, travelled→traveled, …)
#   -lling→ -ling  (modelling→modeling, travelling→traveling, …)
#   Individual words (grey→gray, tyre→tire, kerb→curb, …)

BRITISH_TO_AMERICAN: dict[str, str] = {
    # ---- -ise / -ize -------------------------------------------------------
    "optimise": "optimize",
    "optimised": "optimized",
    "optimising": "optimizing",
    "optimisation": "optimization",
    "recognise": "recognize",
    "recognised": "recognized",
    "recognising": "recognizing",
    "recognition": "recognition",
    "specialise": "specialize",
    "specialised": "specialized",
    "specialising": "specializing",
    "specialisation": "specialization",
    "organise": "organize",
    "organised": "organized",
    "organising": "organizing",
    "organisation": "organization",
    "realise": "realize",
    "realised": "realized",
    "realising": "realizing",
    "minimise": "minimize",
    "minimised": "minimized",
    "minimising": "minimizing",
    "maximise": "maximize",
    "maximised": "maximized",
    "maximising": "maximizing",
    "customise": "customize",
    "customised": "customized",
    "customising": "customizing",
    "customisation": "customization",
    "centralise": "centralize",
    "centralised": "centralized",
    "centralising": "centralizing",
    "standardise": "standardize",
    "standardised": "standardized",
    "standardising": "standardizing",
    "standardisation": "standardization",
    "prioritise": "prioritize",
    "prioritised": "prioritized",
    "prioritising": "prioritizing",
    "digitalise": "digitalize",
    "digitalised": "digitalized",
    "digitalisation": "digitalization",
    "utilise": "utilize",
    "utilised": "utilized",
    "utilising": "utilizing",
    "utilisation": "utilization",
    "normalise": "normalize",
    "normalised": "normalized",
    "normalising": "normalizing",
    "authorise": "authorize",
    "authorised": "authorized",
    "authorising": "authorizing",
    "authorisation": "authorization",
    "summarise": "summarize",
    "summarised": "summarized",
    "summarising": "summarizing",
    "modernise": "modernize",
    "modernised": "modernized",
    "modernising": "modernizing",
    "modernisation": "modernization",
    "harmonise": "harmonize",
    "harmonised": "harmonized",
    "harmonising": "harmonizing",
    "visualise": "visualize",
    "visualised": "visualized",
    "visualising": "visualizing",
    "visualisation": "visualization",
    "characterise": "characterize",
    "characterised": "characterized",
    "categorise": "categorize",
    "categorised": "categorized",
    "emphasise": "emphasize",
    "emphasised": "emphasized",
    "emphasising": "emphasizing",
    "apologise": "apologize",
    "apologised": "apologized",
    "finalise": "finalize",
    "finalised": "finalized",
    "finalising": "finalizing",
    "initialise": "initialize",
    "initialised": "initialized",
    "initialising": "initializing",
    "initialisation": "initialization",
    "mechanise": "mechanize",
    "mechanised": "mechanized",
    "mechanisation": "mechanization",
    "monetise": "monetize",
    "monetised": "monetized",
    "monetising": "monetizing",
    "monetisation": "monetization",
    "subsidise": "subsidize",
    "subsidised": "subsidized",
    "revitalise": "revitalize",
    "revitalised": "revitalized",
    "stabilise": "stabilize",
    "stabilised": "stabilized",
    "stabilisation": "stabilization",
    "capitalise": "capitalize",
    "capitalised": "capitalized",
    "localise": "localize",
    "localised": "localized",
    "localisation": "localization",
    "globalise": "globalize",
    "globalised": "globalized",
    "globalisation": "globalization",
    "hospitalise": "hospitalize",
    "hospitalised": "hospitalized",
    "legalise": "legalize",
    "legalised": "legalized",
    "penalise": "penalize",
    "penalised": "penalized",
    "privatise": "privatize",
    "privatised": "privatized",
    "privatisation": "privatization",
    "scrutinise": "scrutinize",
    "scrutinised": "scrutinized",
    "terrorise": "terrorize",
    "terrorised": "terrorized",
    "immunise": "immunize",
    "immunised": "immunized",
    "immunisation": "immunization",
    "industrialise": "industrialize",
    "industrialised": "industrialized",
    "industrialisation": "industrialization",
    # ---- -our / -or --------------------------------------------------------
    "colour": "color",
    "colours": "colors",
    "coloured": "colored",
    "colouring": "coloring",
    "behaviour": "behavior",
    "behaviours": "behaviors",
    "behavioural": "behavioral",
    "favour": "favor",
    "favours": "favors",
    "favoured": "favored",
    "favourable": "favorable",
    "favourite": "favorite",
    "honour": "honor",
    "honours": "honors",
    "honoured": "honored",
    "honourable": "honorable",
    "humour": "humor",
    "humours": "humors",
    "humoured": "humored",
    "humorous": "humorous",
    "labour": "labor",
    "labours": "labors",
    "laboured": "labored",
    "labouring": "laboring",
    "neighbour": "neighbor",
    "neighbours": "neighbors",
    "neighbouring": "neighboring",
    "neighbourhood": "neighborhood",
    "odour": "odor",
    "odours": "odors",
    "rumour": "rumor",
    "rumours": "rumors",
    "savour": "savor",
    "savours": "savors",
    "savoury": "savory",
    "vapour": "vapor",
    "vapours": "vapors",
    "vigour": "vigor",
    "vigorous": "vigorous",
    "harbour": "harbor",
    "harbours": "harbors",
    "glamour": "glamor",
    "endeavour": "endeavor",
    "endeavours": "endeavors",
    "armour": "armor",
    "armoured": "armored",
    "parlour": "parlor",
    "splendour": "splendor",
    "tumour": "tumor",
    "tumours": "tumors",
    "valour": "valor",
    # ---- -re / -er ---------------------------------------------------------
    "centre": "center",
    "centres": "centers",
    "centred": "centered",
    "metre": "meter",
    "metres": "meters",
    "litre": "liter",
    "litres": "liters",
    "fibre": "fiber",
    "fibres": "fibers",
    "theatre": "theater",
    "theatres": "theaters",
    "lustre": "luster",
    "sombre": "somber",
    "calibre": "caliber",
    "manoeuvre": "maneuver",
    "manoeuvres": "maneuvers",
    "reconnoitre": "reconnoiter",
    "sabre": "saber",
    "spectre": "specter",
    "sceptre": "scepter",
    # ---- -ence / -ense -----------------------------------------------------
    "defence": "defense",
    "defences": "defenses",
    "offence": "offense",
    "offences": "offenses",
    "licence": "license",
    "licences": "licenses",
    "pretence": "pretense",
    "pretences": "pretenses",
    # ---- -yse / -yze -------------------------------------------------------
    "analyse": "analyze",
    "analysed": "analyzed",
    "analysing": "analyzing",
    "paralyse": "paralyze",
    "paralysed": "paralyzed",
    "catalyse": "catalyze",
    "catalysed": "catalyzed",
    # ---- -ogue / -og -------------------------------------------------------
    "catalogue": "catalog",
    "catalogues": "catalogs",
    "dialogue": "dialog",
    "dialogues": "dialogs",
    "analogue": "analog",
    "analogues": "analogs",
    "prologue": "prolog",
    "epilogue": "epilog",
    "monologue": "monolog",
    # ---- -lled / -led,  -lling / -ling -------------------------------------
    "modelled": "modeled",
    "modelling": "modeling",
    "travelled": "traveled",
    "travelling": "traveling",
    "traveller": "traveler",
    "cancelled": "canceled",
    "cancelling": "canceling",
    "counselled": "counseled",
    "counselling": "counseling",
    "counsellor": "counselor",
    "labelled": "labeled",
    "labelling": "labeling",
    "levelled": "leveled",
    "levelling": "leveling",
    "marvelled": "marveled",
    "marvelling": "marveling",
    "marvellous": "marvelous",
    "signalled": "signaled",
    "signalling": "signaling",
    "fuelled": "fueled",
    "fuelling": "fueling",
    "jewellery": "jewelry",
    # ---- Individual words --------------------------------------------------
    "grey": "gray",
    "greys": "grays",
    "tyre": "tire",
    "tyres": "tires",
    "kerb": "curb",
    "kerbs": "curbs",
    "programme": "program",
    "programmes": "programs",
    "aeroplane": "airplane",
    "aeroplanes": "airplanes",
    "aluminium": "aluminum",
    "cheque": "check",
    "cheques": "checks",
    "draught": "draft",
    "draughts": "drafts",
    "gaol": "jail",
    "maths": "math",
    "plough": "plow",
    "ploughs": "plows",
    "pyjamas": "pajamas",
    "sceptical": "skeptical",
    "storey": "story",
    "storeys": "stories",
    "sulphur": "sulfur",
    "whilst": "while",
    "amongst": "among",
    "towards": "toward",
    "forwards": "forward",
    "backwards": "backward",
    "afterwards": "afterward",
    "upwards": "upward",
    "downwards": "downward",
    "inwards": "inward",
    "outwards": "outward",
    "learnt": "learned",
    "burnt": "burned",
    "spelt": "spelled",
    "dreamt": "dreamed",
    "leapt": "leaped",
    "focussed": "focused",
    "focussing": "focusing",
    "enquiry": "inquiry",
    "enquiries": "inquiries",
    "ageing": "aging",
    "judgement": "judgment",
    "acknowledgement": "acknowledgment",
    "fulfilment": "fulfillment",
    "enrolment": "enrollment",
    "skilful": "skillful",
    "wilful": "willful",
    "fulfil": "fulfill",
    "enrol": "enroll",
    "instalment": "installment",
}

# ---------------------------------------------------------------------------
# Pre-compiled lookup regex (built once at import time)
# ---------------------------------------------------------------------------
# Sort keys longest-first so "specialisation" matches before "special".
_SORTED_BRITISH_KEYS: list[str] = sorted(
    BRITISH_TO_AMERICAN.keys(), key=len, reverse=True
)

_BRITISH_PATTERN: re.Pattern[str] = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _SORTED_BRITISH_KEYS) + r")\b",
    re.IGNORECASE,
)


def _match_case(original: str, replacement: str) -> str:
    """Transfer the capitalisation pattern of *original* onto *replacement*.

    Handles three cases:
    - ALL CAPS  → ALL CAPS
    - Title Case → Title Case
    - lower case → lower case
    """
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def normalize_to_american_english(text: str) -> str:
    """Replace British English spellings with their American equivalents.

    Word-boundary aware; preserves the original capitalisation pattern
    (lower, Title, or UPPER) of every replaced word.

    Args:
        text: Input text that may contain British English spellings.

    Returns:
        Text with British spellings converted to American English.
    """
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        word = match.group(0)
        american = BRITISH_TO_AMERICAN[word.lower()]
        return _match_case(word, american)

    return _BRITISH_PATTERN.sub(_replace, text)


# ---------------------------------------------------------------------------
# Emoji removal
# ---------------------------------------------------------------------------
# Comprehensive Unicode ranges covering all modern emoji:
#   - Emoticons, Misc Symbols & Pictographs, Transport & Map, Supplemental
#   - Dingbats, Enclosed Alphanumerics, CJK Compatibility, Flags
#   - Skin-tone modifiers, hair components, ZWJ sequences, variation selectors

_EMOJI_PATTERN: re.Pattern[str] = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
    "\U0001F680-\U0001F6FF"  # Transport & Map
    "\U0001F700-\U0001F77F"  # Alchemical Symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols & Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended-A
    "\U00002600-\U000026FF"  # Misc Symbols
    "\U00002700-\U000027BF"  # Dingbats
    "\U0000FE00-\U0000FE0F"  # Variation Selectors
    "\U0000200D"             # Zero Width Joiner
    "\U000023E9-\U000023F3"  # Media control symbols
    "\U000023F8-\U000023FA"  # Additional media symbols
    "\U0000231A-\U0000231B"  # Watch & Hourglass
    "\U00002934-\U00002935"  # Arrows
    "\U000025AA-\U000025AB"  # Small squares
    "\U000025B6"             # Play button
    "\U000025C0"             # Reverse play
    "\U000025FB-\U000025FE"  # Medium squares
    "\U00002B05-\U00002B07"  # Arrows
    "\U00002B1B-\U00002B1C"  # Large squares
    "\U00002B50"             # Star
    "\U00002B55"             # Circle
    "\U00003030"             # Wavy dash
    "\U0000303D"             # Part alternation mark
    "\U00003297"             # Circled Ideograph Congratulation
    "\U00003299"             # Circled Ideograph Secret
    "\U0001F1E0-\U0001F1FF"  # Regional indicator (flags)
    "\U0001F3FB-\U0001F3FF"  # Skin-tone modifiers
    "]+",
    flags=re.UNICODE,
)


def remove_emojis(text: str) -> str:
    """Remove all Unicode emoji characters from *text*.

    Handles single emoji, flag sequences, skin-tone variants, and
    ZWJ (zero-width joiner) compound emoji.  Non-emoji text—including
    punctuation, numbers, and special characters—is preserved.

    Args:
        text: Input text that may contain emoji characters.

    Returns:
        Text with all emoji characters removed.
    """
    if not text:
        return text
    # Remove emojis, then collapse any resulting double-spaces
    cleaned = _EMOJI_PATTERN.sub("", text)
    cleaned = re.sub(r"  +", " ", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Punctuation & grammar fixes
# ---------------------------------------------------------------------------
# Words that begin with a vowel *sound* for basic a/an detection.
# This is intentionally conservative—only obvious cases are corrected.
_VOWEL_SOUND_PATTERN: re.Pattern[str] = re.compile(
    r"\b[Aa]\s+(?=[AaEeIiOoUu]\w)",
)

# Words starting with a silent 'h' or vowel-sounding 'h' — common cases only
_AN_BEFORE_H_PATTERN: re.Pattern[str] = re.compile(
    r"\b[Aa]\s+(hour|honest|honour|honor|heir|herb)\b",
    re.IGNORECASE,
)


def fix_punctuation_and_grammar(text: str) -> str:
    """Apply punctuation and basic grammar fixes.

    Fixes applied (in order):
    1. Remove stray space **before** punctuation (``,`` ``.`` ``;`` ``:``).
    2. Ensure a single space **after** punctuation (unless end-of-string).
    3. Collapse double (or more) spaces to a single space.
    4. Capitalise the first letter of each sentence.
    5. Correct basic ``a`` → ``an`` before obvious vowel sounds.
    6. Strip trailing whitespace per line.
    7. Append a period to multi-word text that lacks terminal punctuation.

    The function never changes word order or introduces new meaning.

    Args:
        text: Input text to clean up.

    Returns:
        Text with punctuation and grammar fixes applied.
    """
    if not text or not text.strip():
        return text

    # 1. Remove space before punctuation marks
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)

    # 2. Ensure space after punctuation (not at end, not before another punct)
    text = re.sub(r"([,.:;!?])([^\s,.:;!?\d\)])", r"\1 \2", text)

    # 3. Collapse multiple spaces
    text = re.sub(r"  +", " ", text)

    # 4. Capitalise first letter of sentences
    #    Matches: start-of-string or `. ` followed by a lowercase letter.
    def _capitalize_sentence_start(m: re.Match[str]) -> str:
        return m.group(0)[:-1] + m.group(0)[-1].upper()

    text = re.sub(r"(?:^|[.!?]\s+)([a-z])", _capitalize_sentence_start, text)

    # 5. Basic a → an before vowel sounds
    def _a_to_an(m: re.Match[str]) -> str:
        word = m.group(0)
        # Preserve capitalisation of 'A' / 'a'
        prefix = "An" if word[0] == "A" else "an"
        return prefix + word[1:]

    text = _VOWEL_SOUND_PATTERN.sub(_a_to_an, text)
    text = _AN_BEFORE_H_PATTERN.sub(
        lambda m: ("An" if m.group(0)[0] == "A" else "an") + " " + m.group(1),
        text,
    )

    # 6. Strip trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # 7. Append period if multi-word text lacks terminal punctuation
    stripped = text.rstrip()
    if stripped and len(stripped.split()) >= 2 and stripped[-1] not in ".!?:;":
        text = stripped + "."

    return text


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def apply_all_editorial_rules(text: str) -> str:
    """Apply **all** editorial rules in the canonical order.

    Processing pipeline:
    1. Emoji removal
    2. British → American English normalisation
    3. Punctuation & grammar fixes

    Args:
        text: Raw text from any pipeline stage.

    Returns:
        Editorially clean text ready for export or display.
    """
    if not text or not text.strip():
        return text

    text = remove_emojis(text)
    text = normalize_to_american_english(text)
    text = fix_punctuation_and_grammar(text)
    return text
