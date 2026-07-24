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
                message="任务要求生成演示文稿，但没有采集到生成产物。",
            )
        )
        return issues

    failed = [deck for deck in decks if deck.status == "failed"]
    for deck in failed:
        issues.append(
            Issue(
                code="RENDER_FAILED",
                message=f"无法渲染 {Path(deck.artifact_path).name}：{deck.error}",
                evidence={"artifact": deck.artifact_path},
            )
        )

    for deck in decks:
        if deck.kind == "pptx" and deck.status == "rendered" and deck.fidelity != "high":
            issues.append(
                Issue(
                    code="LOW_FIDELITY_RENDER",
                    message=(
                        f"{Path(deck.artifact_path).name} 当前使用 {deck.renderer} 渲染；"
                        "视觉布局判断需要高保真渲染后端。"
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
                    message=f"预期 {expectation.page_count} 页，但渲染产物实际为 {actual} 页。",
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
                message=f"未找到必需内容：{'、'.join(missing)}。",
                evidence={"missing_keywords": missing},
            )
        )

    present = [keyword for keyword in expectation.forbidden_keywords if keyword.casefold() in searchable]
    if present:
        issues.append(
            Issue(
                code="FORBIDDEN_CONTENT",
                message=f"发现禁用内容：{'、'.join(present)}。",
                evidence={"keywords": present},
            )
        )
    return issues
