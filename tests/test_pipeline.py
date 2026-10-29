import random
import unittest
from datetime import datetime, timezone

from pipeline.lessons import build_document, parse_blanks, shuffle_quiz_options
from pipeline.validate import validate_batch, verify_stored_document

FILLER = "Les modèles de langage changent la manière dont nous écrivons du code et des tests. "
SOURCES = [{"title": "Example", "url": "https://example.com/post", "origin": "Blog"}]


def _fill_lesson(blank_count: int = 12) -> dict:
    blanks = " ".join(f"Le mot [[agent{i}|indice {i}]] est utile." for i in range(blank_count))
    return {
        "title": "Agents and tools",
        "titleFr": "Les agents et les outils",
        "difficulty": "B1",
        "sources": SOURCES,
        "scriptMarked": FILLER * 60 + "\n\n" + blanks,
    }


def _quiz_lesson() -> dict:
    return {
        "title": "Quiz lesson",
        "titleFr": "Leçon quiz",
        "difficulty": "B2",
        "sources": SOURCES,
        "script": FILLER * 70,
        "options": [
            {"text": "Résumé correct sur les modèles de langage et le code.", "isCorrect": True},
            {"text": "Résumé faux sur les modèles de langage et les images.", "isCorrect": False},
            {"text": "Résumé faux sur les bases de données et le code source.", "isCorrect": False},
            {"text": "Résumé faux sur les réseaux et les tests automatisés.", "isCorrect": False},
        ],
    }


class ParseBlanksTest(unittest.TestCase):
    def test_round_trip(self):
        parsed = parse_blanks("Un [[agent|personne]] utilise des [[outils]].")
        self.assertEqual(parsed["scriptFull"], "Un agent utilise des outils.")
        self.assertEqual(parsed["passageWithBlanks"], "Un ______ (1) utilise des ______ (2).")
        self.assertEqual(parsed["blanks"][0]["hint"], "personne")
        self.assertIsNone(parsed["blanks"][1]["hint"])


class ValidateTest(unittest.TestCase):
    def test_valid_fill_in_batch(self):
        findings = validate_batch("fill_in_blanks", [("a.json", _fill_lesson())])
        self.assertEqual(findings.errors, [])

    def test_blank_count_enforced(self):
        findings = validate_batch("fill_in_blanks", [("a.json", _fill_lesson(blank_count=3))])
        self.assertTrue(any("blanks" in e for e in findings.errors))

    def test_short_script_rejected(self):
        lesson = _quiz_lesson()
        lesson["script"] = FILLER
        findings = validate_batch("quiz", [("q.json", lesson)])
        self.assertTrue(any("words" in e for e in findings.errors))

    def test_quiz_needs_exactly_one_correct(self):
        lesson = _quiz_lesson()
        lesson["options"][1]["isCorrect"] = True
        findings = validate_batch("quiz", [("q.json", lesson)])
        self.assertTrue(any("exactly one" in e for e in findings.errors))

    def test_hd_voice_rejected(self):
        lesson = _quiz_lesson()
        lesson["voiceName"] = "fr-FR-Vivienne:DragonHDLatestNeural"
        findings = validate_batch("quiz", [("q.json", lesson)])
        self.assertTrue(any("voiceName" in e for e in findings.errors))


class DocumentTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 28, tzinfo=timezone.utc)

    def test_fill_document_verifies(self):
        doc = build_document("fill_in_blanks", _fill_lesson(), run_id="r", created_at=self.now)
        doc["audio"] = {"url": "https://x/y.mp3"}
        self.assertEqual(verify_stored_document(doc), [])
        self.assertTrue(doc["lessonId"].startswith("20261028-agents-and-tools-"))

    def test_shuffle_keeps_correct_answer(self):
        doc = build_document("quiz", _quiz_lesson(), run_id="r", created_at=self.now)
        correct_text = doc["options"][doc["correctIndex"]]
        shuffle_quiz_options(doc, random.Random(7))
        self.assertEqual(doc["options"][doc["correctIndex"]], correct_text)


if __name__ == "__main__":
    unittest.main()
