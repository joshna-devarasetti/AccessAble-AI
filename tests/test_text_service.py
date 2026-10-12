"""
Unit tests for Text Service (Readability & Rule-Based Fallback).
"""

from services.text_service import TextService


def test_clean_text():
    raw = "  “Smart quotes” and   multiple   spaces. \n\n\n\nNew paragraph. "
    cleaned = TextService.clean_text(raw)
    assert '"Smart quotes"' in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned


def test_syllable_count():
    assert TextService.count_syllables_word("cat") == 1
    assert TextService.count_syllables_word("simple") == 2
    assert TextService.count_syllables_word("accessibility") >= 5


def test_analyze_readability():
    sample = "The quick brown fox jumps over the lazy dog. It is a very easy sentence to read."
    stats = TextService.analyze_readability(sample)
    assert stats["word_count"] > 10
    assert stats["sentence_count"] == 2
    assert stats["reading_ease"] > 70
    assert stats["grade_level"] < 8.0
    assert "reading_level_label" in stats


def test_analyze_readability_empty():
    stats = TextService.analyze_readability("")
    assert stats["word_count"] == 0
    assert stats["reading_ease"] == 0.0


def test_rule_based_simplification():
    complex_text = "We shall utilize preventative methods to facilitate optimal operational status and terminate risks."
    res = TextService.rule_based_simplify(complex_text)
    
    assert res["is_ai_generated"] is False
    assert res["method"] == "rule-based-fallback"
    assert "use" in res["simplified_text"].lower()
    assert "help" in res["simplified_text"].lower()
    assert "end" in res["simplified_text"].lower()
    assert res["substitutions_count"] >= 3
    assert "Notice:" in res["disclaimer"]


def test_clean_simplified_text_strips_intros():
    sample1 = "Here is the simplified text:\n\nPeople should follow these instructions."
    assert TextService.clean_simplified_text(sample1) == "People should follow these instructions."

    sample2 = "Here's the simplified version:\n\nDrive carefully on residential roads."
    assert TextService.clean_simplified_text(sample2) == "Drive carefully on residential roads."

    sample3 = "Sure! Here is the text in plain English:\nTake one pill daily with food."
    assert TextService.clean_simplified_text(sample3) == "Take one pill daily with food."

    sample4 = "Simplified version: Wash hands with soap and water."
    assert TextService.clean_simplified_text(sample4) == "Wash hands with soap and water."


def test_clean_simplified_text_strips_quotes():
    sample1 = '"Blood pressure is very high. Take medicine right away."'
    assert TextService.clean_simplified_text(sample1) == "Blood pressure is very high. Take medicine right away."

    sample2 = "“The patient has a sore throat.”"
    assert TextService.clean_simplified_text(sample2) == "The patient has a sore throat."


def test_clean_simplified_text_strips_trailing_notes_and_closers():
    sample1 = "The patient should rest for three days.\n\nNote: Preserved medical dosage and timeline."
    assert TextService.clean_simplified_text(sample1) == "The patient should rest for three days."

    sample2 = "Smoking causes severe damage to lungs.\n\nExplanation: Replaced technical jargon with plain words."
    assert TextService.clean_simplified_text(sample2) == "Smoking causes severe damage to lungs."

    sample3 = "Eat fresh fruits and vegetables daily.\n\nHope this helps!"
    assert TextService.clean_simplified_text(sample3) == "Eat fresh fruits and vegetables daily."


def test_clean_simplified_text_combined():
    combined = 'Here\'s the simplified version:\n\n"The heart works hard to pump blood."\n\nNote: All medical facts preserved.'
    assert TextService.clean_simplified_text(combined) == "The heart works hard to pump blood."

