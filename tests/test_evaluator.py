import tempfile
import unittest
from pathlib import Path

from ppt_quality_pipeline.evaluator import evaluate
from ppt_quality_pipeline.models import Expectation, RenderedDeck


class EvaluatorTests(unittest.TestCase):
    def test_flags_page_count_and_missing_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifact = root / "deck.html"
            artifact.write_text("<html><body>Evidence and workflow</body></html>", encoding="utf-8")
            artifacts = [
                {
                    "role": "generated",
                    "kind": "html",
                    "staged_path": "deck.html",
                }
            ]
            decks = [
                RenderedDeck(
                    artifact_path="deck.html",
                    kind="html",
                    pages=["page_001.png", "page_002.png"],
                    page_count=2,
                    status="rendered",
                )
            ]
            issues = evaluate(
                Expectation(page_count=3, required_keywords=["evidence", "human review"]),
                artifacts,
                decks,
                root,
            )
            self.assertEqual(
                {issue.code for issue in issues},
                {"PAGE_COUNT_MISMATCH", "MISSING_REQUIRED_CONTENT"},
            )

    def test_flags_missing_generated_output(self) -> None:
        issues = evaluate(Expectation(page_count=1), [], [], Path("."))
        self.assertEqual([issue.code for issue in issues], ["NO_OUTPUT"])

    def test_flags_low_fidelity_pptx_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifact = root / "deck.pptx"
            artifact.write_bytes(b"placeholder")
            artifacts = [{"role": "generated", "kind": "pptx", "staged_path": "deck.pptx"}]
            decks = [
                RenderedDeck(
                    artifact_path="deck.pptx",
                    kind="pptx",
                    pages=["page_001.png"],
                    page_count=1,
                    status="rendered",
                    renderer="pptx-text-preview",
                    fidelity="low",
                )
            ]
            issues = evaluate(Expectation(page_count=1), artifacts, decks, root)
            self.assertEqual([issue.code for issue in issues], ["LOW_FIDELITY_RENDER"])

    def test_passes_matching_expectations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifact = root / "deck.html"
            artifact.write_text("<p>Human review with evidence.</p>", encoding="utf-8")
            artifacts = [{"role": "generated", "kind": "html", "staged_path": "deck.html"}]
            decks = [
                RenderedDeck(
                    artifact_path="deck.html",
                    kind="html",
                    pages=["page_001.png"],
                    page_count=1,
                    status="rendered",
                )
            ]
            issues = evaluate(
                Expectation(page_count=1, required_keywords=["human review", "evidence"]),
                artifacts,
                decks,
                root,
            )
            self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
