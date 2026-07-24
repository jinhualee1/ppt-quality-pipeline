import base64
import json
import tempfile
import unittest
from pathlib import Path

from ppt_quality_pipeline.pipeline import Pipeline

ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class PipelineTests(unittest.TestCase):
    def test_local_image_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "slide.png"
            image.write_bytes(ONE_PIXEL_PNG)
            tasks = root / "tasks.jsonl"
            tasks.write_text(
                json.dumps(
                    {
                        "id": "image-demo",
                        "query": "Review this rendered slide.",
                        "artifacts": [{"path": "slide.png", "kind": "image", "role": "generated"}],
                        "expectation": {"page_count": 1},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            output = root / "run"
            report = Pipeline().run(tasks, output)
            self.assertEqual(report["summary"]["passed"], 1)
            self.assertEqual(report["summary"]["rendered_pages"], 1)
            self.assertTrue((output / "report.json").is_file())
            self.assertTrue((output / "report.csv").is_file())

    def test_refuses_to_overwrite_unmarked_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "existing"
            output.mkdir()
            (output / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                Pipeline.prepare_run_dir(output, overwrite=True)


if __name__ == "__main__":
    unittest.main()
