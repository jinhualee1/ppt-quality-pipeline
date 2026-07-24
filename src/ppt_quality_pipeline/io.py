from __future__ import annotations

import json
import re
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import Task


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_tasks(path: Path) -> list[Task]:
    path = path.resolve()
    if path.suffix.lower() == ".jsonl":
        values = [
            json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
        ]
    else:
        raw = read_json(path)
        values = raw if isinstance(raw, list) else raw.get("tasks", [])
    tasks = [Task.from_dict(value, path.parent) for value in values]
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Task IDs must be unique.")
    return tasks


def safe_name(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return (cleaned or fallback)[:100]


def copy_artifact(source: Path, destination_dir: Path) -> Path:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Artifact does not exist: {source}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / safe_name(source.name, "artifact")
    if destination.exists() and destination.read_bytes() == source.read_bytes():
        return destination
    if destination.exists():
        destination = destination_dir / f"{destination.stem}_copy{destination.suffix}"
    shutil.copy2(source, destination)
    return destination


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def iter_files(root: Path, suffixes: Iterable[str]) -> Iterable[Path]:
    wanted = {suffix.lower() for suffix in suffixes}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in wanted:
            yield path
