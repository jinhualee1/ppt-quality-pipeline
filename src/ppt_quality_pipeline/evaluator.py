from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Expectation, Issue, RenderedDeck
from .text import extract_text


def evaluate(
    expectation: Expectation,
    artifacts: list[dict[str, Any]],
    decks: list[RenderedDeck],
    run_dir: Path,
) -> list[Issue]:
    issues: list[Issue] = []
    generated = [artifact for artifact in artifacts if artifact.get("role") == "generated"]
    if not generated:
        issues.append(
            Issue(
                code="NO_OUTPUT",
                message="The task expected a generated presentation, but no generated artifact was collected.",
            )
        )
        return issues

    failed = [deck for deck in decks if deck.status == "failed"]
    for deck in failed:
        issues.append(
            Issue(
                code="RENDER_FAILED",
                message=f"Could not render {Path(deck.artifact_path).name}: {deck.error}",
                evidence={"artifact": deck.artifact_path},
            )
        )

    for deck in decks:
        if deck.kind == "pptx" and deck.status == "rendered" and deck.fidelity != "high":
            issues.append(
                Issue(
                    code="LOW_FIDELITY_RENDER",
                    message=(
                        f"{Path(deck.artifact_path).name} was rendered with "
                        f"{deck.renderer}; visual layout findings require a high-fidelity renderer."
                    ),
                    severity="warning",
                    evidence={"artifact": deck.artifact_path, "renderer": deck.renderer},
                )
            )

    rendered = [deck for deck in decks if deck.status == "rendered" and deck.page_count > 0]
    if expectation.page_count is not None and rendered:
        actual = rendered[-1].page_count
        if actual != expectation.page_count:
            issues.append(
                Issue(
                    code="PAGE_COUNT_MISMATCH",
                    message=f"Expected {expectation.page_count} slides, but the rendered artifact has {actual}.",
                    evidence={"expected": expectation.page_count, "actual": actual},
                )
            )

    combined_text = []
    for artifact in generated:
        source = run_dir / artifact["staged_path"]
        try:
            combined_text.append(extract_text(source, artifact["kind"]))
        except (OSError, ValueError):
            continue
    searchable = " ".join(combined_text).casefold()

    missing = [keyword for keyword in expectation.required_keywords if keyword.casefold() not in searchable]
    if missing:
        issues.append(
            Issue(
                code="MISSING_REQUIRED_CONTENT",
                message=f"Required content was not found: {', '.join(missing)}.",
                evidence={"missing_keywords": missing},
            )
        )

    present = [keyword for keyword in expectation.forbidden_keywords if keyword.casefold() in searchable]
    if present:
        issues.append(
            Issue(
                code="FORBIDDEN_CONTENT",
                message=f"Forbidden content was found: {', '.join(present)}.",
                evidence={"keywords": present},
            )
        )
    return issues
