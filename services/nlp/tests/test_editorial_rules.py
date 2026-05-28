import pytest
from app.humanizer.editorial_rules import (
    normalize_to_american_english,
    remove_emojis,
    fix_punctuation_and_grammar,
    apply_all_editorial_rules
)

def test_british_to_american_conversion():
    assert normalize_to_american_english("We should optimise the colour scheme.") == "We should optimize the color scheme."
    assert normalize_to_american_english("Analyse this behaviour.") == "Analyze this behavior."
    assert normalize_to_american_english("Move towards the centre.") == "Move toward the center."
    # Case preservation
    assert normalize_to_american_english("COLOUR") == "COLOR"
    assert normalize_to_american_english("Optimise") == "Optimize"

def test_emoji_removal():
    assert remove_emojis("Hello World 🎨🚀!") == "Hello World !"
    assert remove_emojis("Slide text 👩‍💻 is clean") == "Slide text is clean"
    # Ensure double spacing created by emoji removal is collapsed
    assert remove_emojis("A  B") == "A B"

def test_punctuation_and_grammar_fixes():
    # Spacing around punctuation
    assert fix_punctuation_and_grammar("Hello , world .") == "Hello, world."
    # Sentence capitalization
    assert fix_punctuation_and_grammar("this is test one. that is test two.") == "This is test one. That is test two."
    # Basic a -> an
    assert fix_punctuation_and_grammar("A apple and a orange.") == "An apple and an orange."
    assert fix_punctuation_and_grammar("It takes a hour.") == "It takes an hour."
    # Terminal period for multi-word texts
    assert fix_punctuation_and_grammar("Needs a period") == "Needs a period."
    assert fix_punctuation_and_grammar("Heading") == "Heading"  # Single word, no period

def test_apply_all_editorial_rules():
    raw = "let's optimise the colour scheme 🎨 . it takes a hour"
    expected = "Let's optimize the color scheme. It takes an hour."
    assert apply_all_editorial_rules(raw) == expected
