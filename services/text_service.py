"""
Text Service
Calculates readability metrics (Flesch-Kincaid Grade Level, Flesch Reading Ease),
cleans text, and provides an explicitly-labeled rule-based text helper fallback.
"""

import re
import math
from typing import Dict, Any, List, Tuple


class TextService:
    # Common complex to plain English word mappings
    PLAIN_ENGLISH_DICTIONARY = {
        "utilize": "use",
        "utilizes": "uses",
        "utilized": "used",
        "utilizing": "using",
        "commence": "start",
        "commences": "starts",
        "commenced": "started",
        "terminate": "end",
        "terminated": "ended",
        "subsequently": "later",
        "consequently": "so",
        "nevertheless": "however",
        "demonstrate": "show",
        "demonstrates": "shows",
        "demonstrated": "showed",
        "approximately": "about",
        "implement": "put in place",
        "implemented": "set up",
        "sufficient": "enough",
        "endeavor": "try",
        "facilitate": "help",
        "facilitates": "helps",
        "facilitated": "helped",
        "disseminate": "spread",
        "advantageous": "helpful",
        "fundamental": "basic",
        "imperative": "vital",
        "substantial": "large",
        "expedite": "speed up",
        "ascertain": "find out",
        "cognizant": "aware",
        "elucidate": "explain",
        "ameliorate": "improve",
        "erroneous": "wrong",
        "inquire": "ask",
        "modification": "change",
        "modifications": "changes",
        "necessitate": "need",
        "optimal": "best",
        "prescribe": "order",
        "procure": "get",
        "reimburse": "pay back",
        "remuneration": "pay",
        "transmit": "send",
        "transmits": "sends",
        "transmitted": "sent",
        "unprecedented": "new and unusual",
        "vicinity": "area",
        "furthermore": "also",
        "moreover": "also",
        "heretofore": "before now",
        "whilst": "while",
        "whereby": "by which"
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """Strip non-printable chars, normalize spaces and quotes."""
        if not text:
            return ""
        # Normalize typographic quotes and dashes
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        text = text.replace("—", " - ").replace("–", " - ")
        # Collapse multiple spaces and multiple newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @staticmethod
    def count_syllables_word(word: str) -> int:
        """Heuristic syllable counter for English words."""
        word = word.lower().strip()
        if not word:
            return 0
        if len(word) <= 3:
            return 1
        
        # Remove punctuation
        word = re.sub(r"[^a-z]", "", word)
        if not word:
            return 1

        # Handle silent e at end
        if word.endswith("e") and not word.endswith("le") and len(word) > 2:
            word = word[:-1]

        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel

        return max(1, count)

    @classmethod
    def clean_simplified_text(cls, raw_text: str) -> str:
        """
        Strips introductory preambles, surrounding quotation marks,
        trailing notes, explanations, and commentary from LLM output.
        Returns ONLY the pure simplified text.
        """
        if not raw_text:
            return ""

        text = raw_text.strip()

        # 1. Strip markdown code fences if present (e.g. ```text ... ```)
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                text = "\n".join(lines[1:-1]).strip()

        # 2. Strip leading introductory phrases (case-insensitive)
        intro_patterns = [
            r"^(?:as\s+requested\s*,?\s*)?(?:here(?:\s+is|['’]?s|\s+are)|below\s+is|sure\s*[,!.]?\s*here(?:\s+is|['’]?s))\s+[^.\n:]*(?:simplified|simpler|plain english|rewritten|version|text)[^.\n:]*[:.]?\s*\n*",
            r"^(?:here(?:\s+is|['’]?s|\s+are)|below\s+is)\s+the\s+rewritten\s+text[:.]?\s*\n*",
            r"^(?:i\s+(?:have|can)\s+simplified\b.*?)[:.]?\s*\n*",
            r"^(?:simplified|simpler|plain english|rewritten)\s*(?:text|version)?\s*[:.]?\s*\n*",
            r"^in\s+(?:simple|plain)\s+(?:english|words|terms)\s*[:.]?\s*\n*",
            r"^(?:here(?:\s+is|['’]?s|\s+are)|here\s+you\s+go)\s*[:.]?\s*\n*"
        ]
        for pat in intro_patterns:
            text = re.sub(pat, "", text, count=1, flags=re.IGNORECASE).strip()

        # 3. Strip trailing explanations, notes, comments, or conversational closers
        trail_patterns = [
            r"\n+\s*(?:note|notes|explanation|comments?|key changes?|disclaimer)\s*:.*$",
            r"\n+\s*(?:hope this helps|let me know if you need|let me know if you have|please let me know|feel free to ask).*$"
        ]
        for pat in trail_patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE | re.DOTALL).strip()

        # 4. Strip surrounding quotation marks
        quote_pairs = [
            ('"', '"'),
            ("'", "'"),
            ("“", "”"),
            ("‘", "’")
        ]
        changed = True
        while changed:
            changed = False
            text = text.strip()
            for q_start, q_end in quote_pairs:
                if text.startswith(q_start) and text.endswith(q_end) and len(text) >= 2:
                    text = text[len(q_start):-len(q_end)].strip()
                    changed = True

        # 5. Clean excess whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    @classmethod
    def analyze_readability(cls, text: str) -> Dict[str, Any]:
        """
        Calculates word count, sentence count, Flesch Reading Ease,
        and Flesch-Kincaid Grade Level based strictly on actual text.
        """
        cleaned = cls.clean_text(text)
        if not cleaned:
            return {
                "word_count": 0,
                "sentence_count": 0,
                "char_count": 0,
                "reading_ease": 0.0,
                "grade_level": 0.0,
                "reading_level_label": "No text",
                "estimated_read_minutes": 0.0
            }

        words = re.findall(r"\b[A-Za-z0-9'-]+\b", cleaned)
        if not words:
            return {
                "word_count": 0,
                "sentence_count": 0,
                "char_count": len(cleaned),
                "reading_ease": 0.0,
                "grade_level": 0.0,
                "reading_level_label": "No words",
                "estimated_read_minutes": 0.0
            }

        # Sentences split by ., !, ?
        sentences = [s.strip() for s in re.split(r"[.!?]+(?:\s+|$)", cleaned) if s.strip()]
        sentence_count = max(1, len(sentences))

        word_count = len(words)
        char_count = len(cleaned)

        total_syllables = sum(cls.count_syllables_word(w) for w in words)

        # Flesch Reading Ease Formula:
        # 206.835 - 1.015 * (total words / total sentences) - 84.6 * (total syllables / total words)
        words_per_sentence = word_count / sentence_count
        syllables_per_word = total_syllables / word_count

        reading_ease = 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)
        reading_ease = round(max(0.0, min(100.0, reading_ease)), 1)

        # Flesch-Kincaid Grade Level Formula:
        # 0.39 * (total words / total sentences) + 11.8 * (total syllables / total words) - 15.59
        grade_level = (0.39 * words_per_sentence) + (11.8 * syllables_per_word) - 15.59
        grade_level = round(max(0.0, grade_level), 1)

        # Label based on Flesch Reading Ease
        if reading_ease >= 90:
            reading_level_label = "Very Easy (5th grade)"
        elif reading_ease >= 80:
            reading_level_label = "Easy (6th grade)"
        elif reading_ease >= 70:
            reading_level_label = "Fairly Easy (7th grade)"
        elif reading_ease >= 60:
            reading_level_label = "Plain English (8th-9th grade)"
        elif reading_ease >= 50:
            reading_level_label = "Fairly Difficult (High School)"
        elif reading_ease >= 30:
            reading_level_label = "Difficult (College level)"
        else:
            reading_level_label = "Very Difficult (Academic/Technical)"

        # Estimated reading time based on typical 200 words per minute
        estimated_read_minutes = round(word_count / 200.0, 1)

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "char_count": char_count,
            "reading_ease": reading_ease,
            "grade_level": grade_level,
            "reading_level_label": reading_level_label,
            "estimated_read_minutes": estimated_read_minutes,
            "avg_words_per_sentence": round(words_per_sentence, 1)
        }

    @classmethod
    def rule_based_simplify(cls, text: str) -> Dict[str, Any]:
        """
        EXPLICITLY LABELED non-AI fallback text simplifier.
        Used ONLY when Ollama is offline or no model is loaded.
        Does not pretend to be AI output.
        """
        cleaned = cls.clean_text(text)
        if not cleaned:
            return {
                "simplified_text": "",
                "method": "rule-based-fallback",
                "is_ai_generated": False,
                "substitutions_made": 0,
                "notes": "Empty input."
            }

        # 1. Substitute complex vocabulary
        substitutions = 0
        working_text = cleaned
        for complex_word, simple_word in cls.PLAIN_ENGLISH_DICTIONARY.items():
            pattern = re.compile(rf"\b{complex_word}\b", re.IGNORECASE)
            matches = pattern.findall(working_text)
            if matches:
                substitutions += len(matches)
                # Preserve capitalization
                def replace_match(m):
                    orig = m.group(0)
                    if orig.isupper():
                        return simple_word.upper()
                    elif orig[0].isupper():
                        return simple_word.capitalize()
                    return simple_word

                working_text = pattern.sub(replace_match, working_text)

        # 2. Break very long sentences (> 25 words) joined by semicolons, dashes or coordinating conjunctions
        paragraphs = working_text.split("\n\n")
        reformatted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # Replace semicolons with periods to shorten sentences
            para = re.sub(r";\s*", ". ", para)
            
            # Sentence level break down
            raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
            simplified_sentences = []
            for s in raw_sentences:
                words = s.split()
                # If a sentence is very long, look for " which ", " and also ", " however, "
                if len(words) > 22:
                    s_broken = re.sub(r",\s+(which|whereas|whilst)\s+", ". This ", s, flags=re.IGNORECASE)
                    simplified_sentences.append(s_broken)
                else:
                    simplified_sentences.append(s)

            reformatted_paragraphs.append(" ".join(simplified_sentences))

        final_simplified = "\n\n".join(reformatted_paragraphs)

        before_stats = cls.analyze_readability(cleaned)
        after_stats = cls.analyze_readability(final_simplified)

        return {
            "simplified_text": final_simplified,
            "method": "rule-based-fallback",
            "is_ai_generated": False,
            "disclaimer": "Notice: This text was simplified using deterministic rule-based pattern matching (plain English substitution and sentence splitting) because a local Ollama AI model was not active.",
            "substitutions_count": substitutions,
            "before_readability": before_stats,
            "after_readability": after_stats
        }
