from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Artifact:
    path: str
    kind: str = "auto"
    role: str = "generated"
    label: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Artifact:
        return cls(
            path=str(value["path"]),
            kind=str(value.get("kind", "auto")),
            role=str(value.get("role", "generated")),
            label=str(value.get("label", "")),
        )


@dataclass(slots=True)
class Expectation:
    page_count: int | None = None
    required_keywords: list[str] = field(default_factory=list)
    forbidden_keywords: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> Expectation:
        value = value or {}
        page_count = value.get("page_count")
        return cls(
            page_count=int(page_count) if page_count is not None else None,
            required_keywords=[str(item) for item in value.get("required_keywords", [])],
            forbidden_keywords=[str(item) for item in value.get("forbidden_keywords", [])],
        )


@dataclass(slots=True)
class Task:
    id: str
    query: str
    artifacts: list[Artifact] = field(default_factory=list)
    expectation: Expectation = field(default_factory=Expectation)
    metadata: dict[str, Any] = field(default_factory=dict)
    source_dir: Path = field(default_factory=Path, repr=False)

    @classmethod
    def from_dict(cls, value: dict[str, Any], source_dir: Path) -> Task:
        task_id = str(value.get("id", "")).strip()
        if not task_id:
            raise ValueError("Each task requires a non-empty 'id'.")
        return cls(
            id=task_id,
            query=str(value.get("query", "")).strip(),
            artifacts=[Artifact.from_dict(item) for item in value.get("artifacts", [])],
            expectation=Expectation.from_dict(value.get("expectation")),
            metadata=dict(value.get("metadata", {})),
            source_dir=source_dir,
        )


@dataclass(slots=True)
class Issue:
    code: str
    message: str
    severity: str = "error"
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RenderedDeck:
    artifact_path: str
    kind: str
    pages: list[str] = field(default_factory=list)
    page_count: int = 0
    status: str = "pending"
    renderer: str = ""
    error: str = ""


@dataclass(slots=True)
class ItemResult:
    id: str
    query: str
    status: str
    artifacts: list[dict[str, Any]]
    decks: list[RenderedDeck]
    issues: list[Issue]
    expectation: Expectation
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
