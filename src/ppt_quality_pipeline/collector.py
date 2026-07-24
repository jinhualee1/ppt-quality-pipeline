from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .io import copy_artifact, relative_posix, safe_name, write_json
from .models import Task


def infer_kind(path: Path, declared: str) -> str:
    if declared and declared != "auto":
        return declared.lower()
    return {
        ".html": "html",
        ".htm": "html",
        ".pptx": "pptx",
        ".pdf": "pdf",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".webp": "image",
    }.get(path.suffix.lower(), "file")


class LocalCollector:
    """Stages local artifacts into a deterministic run directory."""

    def collect(self, task: Task, run_dir: Path) -> dict[str, Any]:
        item_dir = run_dir / "items" / safe_name(task.id)
        artifact_dir = item_dir / "artifacts"
        staged: list[dict[str, Any]] = []
        errors: list[str] = []

        for artifact in task.artifacts:
            source = Path(artifact.path)
            if not source.is_absolute():
                source = task.source_dir / source
            try:
                copied = copy_artifact(source, artifact_dir)
                staged.append(
                    {
                        **asdict(artifact),
                        "kind": infer_kind(copied, artifact.kind),
                        "source_name": source.name,
                        "staged_path": relative_posix(copied, run_dir),
                    }
                )
            except (FileNotFoundError, OSError) as exc:
                errors.append(str(exc))

        manifest = {
            "id": task.id,
            "query": task.query,
            "expectation": asdict(task.expectation),
            "metadata": task.metadata,
            "artifacts": staged,
            "errors": errors,
        }
        write_json(item_dir / "manifest.json", manifest)
        return manifest
