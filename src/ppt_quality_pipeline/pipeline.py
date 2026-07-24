from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .collector import LocalCollector
from .evaluator import evaluate
from .exporter import export_csv, export_json_summary
from .io import load_tasks, safe_name, write_json
from .models import ItemResult
from .renderers import render_artifact


class Pipeline:
    def __init__(self, collector: LocalCollector | None = None) -> None:
        self.collector = collector or LocalCollector()

    @staticmethod
    def prepare_run_dir(run_dir: Path, overwrite: bool = False) -> Path:
        run_dir = run_dir.resolve()
        marker = run_dir / ".pqp-run"
        if run_dir.exists() and any(run_dir.iterdir()):
            if not overwrite:
                raise FileExistsError(f"Run directory is not empty: {run_dir}")
            if not marker.is_file():
                raise RuntimeError(f"Refusing to overwrite an unmarked directory: {run_dir}")
            shutil.rmtree(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text("PPT Quality Pipeline run directory\n", encoding="ascii")
        return run_dir

    def run(
        self,
        task_file: Path,
        run_dir: Path,
        *,
        overwrite: bool = False,
        render: bool = True,
    ) -> dict:
        run_dir = self.prepare_run_dir(run_dir, overwrite=overwrite)
        tasks = load_tasks(task_file)
        started = datetime.now(timezone.utc)
        results: list[ItemResult] = []

        for task in tasks:
            manifest = self.collector.collect(task, run_dir)
            decks = []
            if render:
                for index, artifact in enumerate(manifest["artifacts"], 1):
                    if artifact.get("role") != "generated":
                        continue
                    output_dir = (
                        run_dir
                        / "items"
                        / safe_name(task.id)
                        / "renders"
                        / f"{index:02d}_{safe_name(Path(artifact['staged_path']).stem)}"
                    )
                    decks.append(render_artifact(artifact, run_dir, output_dir))
            issues = evaluate(task.expectation, manifest["artifacts"], decks, run_dir)
            issues.extend(
                {
                    "code": "COLLECTION_FAILED",
                    "message": error,
                    "severity": "error",
                    "evidence": {},
                }
                for error in manifest["errors"]
            )
            normalized_issues = []
            for issue in issues:
                if isinstance(issue, dict):
                    from .models import Issue

                    normalized_issues.append(Issue(**issue))
                else:
                    normalized_issues.append(issue)
            status = "passed" if not normalized_issues else "needs_review"
            results.append(
                ItemResult(
                    id=task.id,
                    query=task.query,
                    status=status,
                    artifacts=manifest["artifacts"],
                    decks=decks,
                    issues=normalized_issues,
                    expectation=task.expectation,
                    metadata=task.metadata,
                )
            )

        finished = datetime.now(timezone.utc)
        report = {
            "schema_version": "1.0",
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "source": str(task_file.resolve()),
            "summary": {
                "items": len(results),
                "passed": sum(result.status == "passed" for result in results),
                "needs_review": sum(result.status == "needs_review" for result in results),
                "rendered_pages": sum(
                    deck.page_count for result in results for deck in result.decks if deck.status == "rendered"
                ),
            },
            "items": [result.to_dict() for result in results],
        }
        write_json(run_dir / "report.json", report)
        export_csv(run_dir)
        export_json_summary(run_dir)
        return report
