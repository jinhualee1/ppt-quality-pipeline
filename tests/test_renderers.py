import os
import unittest
from pathlib import Path
from unittest.mock import patch

from ppt_quality_pipeline.models import RenderedDeck
from ppt_quality_pipeline.renderers import RenderError, pdftoppm_available, render_pptx


class PptxRendererTests(unittest.TestCase):
    @patch("ppt_quality_pipeline.renderers.subprocess.run")
    @patch("ppt_quality_pipeline.renderers.pdftoppm_executable")
    def test_pdftoppm_probe_rejects_broken_wrapper(self, executable, run) -> None:
        executable.return_value = "pdftoppm"
        run.return_value.returncode = 1
        self.assertFalse(pdftoppm_available())

    @patch("ppt_quality_pipeline.renderers.render_pptx_powerpoint")
    def test_explicit_powerpoint_backend(self, powerpoint) -> None:
        expected = RenderedDeck(
            artifact_path="deck.pptx",
            kind="pptx",
            pages=["page_001.png"],
            page_count=1,
            status="rendered",
            renderer="microsoft-powerpoint",
            fidelity="high",
        )
        powerpoint.return_value = expected
        with patch.dict(os.environ, {"PQP_PPTX_BACKEND": "powerpoint"}):
            actual = render_pptx(Path("deck.pptx"), Path("pages"), Path("."))
        self.assertIs(actual, expected)
        powerpoint.assert_called_once()

    @patch("ppt_quality_pipeline.renderers.render_pptx_preview")
    @patch("ppt_quality_pipeline.renderers.render_pptx_libreoffice")
    @patch("ppt_quality_pipeline.renderers.render_pptx_powerpoint")
    def test_auto_backend_records_failures_before_preview(
        self,
        powerpoint,
        libreoffice,
        preview,
    ) -> None:
        powerpoint.side_effect = RenderError("not installed")
        libreoffice.side_effect = RenderError("not installed")
        preview.return_value = RenderedDeck(
            artifact_path="deck.pptx",
            kind="pptx",
            status="rendered",
            renderer="pptx-text-preview",
            fidelity="low",
        )
        with patch.dict(os.environ, {"PQP_PPTX_BACKEND": "auto"}, clear=False):
            result = render_pptx(Path("deck.pptx"), Path("pages"), Path("."))
        self.assertEqual(result.fidelity, "low")
        warnings = preview.call_args.args[3]
        self.assertEqual(len(warnings), 2)
        self.assertIn("PowerPoint", warnings[0])
        self.assertIn("LibreOffice", warnings[1])

    def test_rejects_unknown_backend(self) -> None:
        with (
            patch.dict(os.environ, {"PQP_PPTX_BACKEND": "unknown"}, clear=False),
            self.assertRaises(RenderError),
        ):
            render_pptx(Path("deck.pptx"), Path("pages"), Path("."))


if __name__ == "__main__":
    unittest.main()
