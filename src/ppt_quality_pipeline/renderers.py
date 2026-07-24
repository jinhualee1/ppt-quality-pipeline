from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .io import relative_posix, write_json
from .models import RenderedDeck
from .text import extract_pptx_text


class RenderError(RuntimeError):
    pass


def _find_executable(env_name: str, candidates: list[str]) -> str | None:
    configured = os.environ.get(env_name, "").strip()
    if configured and Path(configured).is_file():
        return configured
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        if Path(candidate).is_file():
            return candidate
    return None


def _node_executable() -> str | None:
    return _find_executable(
        "PQP_NODE",
        [
            "node",
            r"C:\Program Files\nodejs\node.exe",
        ],
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def render_html(source: Path, output_dir: Path, run_dir: Path) -> RenderedDeck:
    node = _node_executable()
    if not node:
        raise RenderError("Node.js was not found. Set PQP_NODE or install Node.js.")
    packaged_helper = Path(__file__).resolve().parent / "browser" / "render_html.mjs"
    source_helper = _project_root() / "scripts" / "render_html.mjs"
    helper = packaged_helper if packaged_helper.is_file() else source_helper
    if not helper.is_file():
        raise RenderError(f"HTML renderer helper is missing: {helper}")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        node,
        str(helper),
        "--input",
        str(source),
        "--output",
        str(output_dir),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RenderError(detail or "HTML renderer failed.")
    manifest_path = output_dir / "render_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = [relative_posix(output_dir / name, run_dir) for name in manifest["pages"]]
    return RenderedDeck(
        artifact_path=relative_posix(source, run_dir),
        kind="html",
        pages=pages,
        page_count=len(pages),
        status="rendered",
        renderer="playwright",
    )


def render_image(source: Path, output_dir: Path, run_dir: Path) -> RenderedDeck:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"page_001{source.suffix.lower()}"
    shutil.copy2(source, destination)
    return RenderedDeck(
        artifact_path=relative_posix(source, run_dir),
        kind="image",
        pages=[relative_posix(destination, run_dir)],
        page_count=1,
        status="rendered",
        renderer="image-copy",
    )


def render_pdf(source: Path, output_dir: Path, run_dir: Path) -> RenderedDeck:
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RenderError("PDF rendering requires the optional 'pdf' dependency: pip install -e .[pdf]") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    pages: list[str] = []
    with fitz.open(source) as document:
        for index, page in enumerate(document):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            destination = output_dir / f"page_{index + 1:03d}.png"
            pixmap.save(destination)
            pages.append(relative_posix(destination, run_dir))
    return RenderedDeck(
        artifact_path=relative_posix(source, run_dir),
        kind="pdf",
        pages=pages,
        page_count=len(pages),
        status="rendered",
        renderer="pymupdf",
    )


def _pptx_slide_texts(source: Path) -> list[str]:
    try:
        from pptx import Presentation  # type: ignore[import-not-found]
    except ImportError:
        text = extract_pptx_text(source)
        return [text] if text else []

    deck = Presentation(source)
    slide_texts: list[str] = []
    for slide in deck.slides:
        chunks = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and str(shape.text).strip():
                chunks.append(str(shape.text).strip())
        slide_texts.append("\n".join(chunks))
    return slide_texts


def render_pptx_preview(source: Path, output_dir: Path, run_dir: Path) -> RenderedDeck:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RenderError("PPTX fallback rendering requires Pillow.") from exc

    slide_texts = _pptx_slide_texts(source)
    if not slide_texts:
        raise RenderError("No slides could be read from the PPTX file.")
    output_dir.mkdir(parents=True, exist_ok=True)
    pages: list[str] = []
    font = ImageFont.load_default()
    for index, text in enumerate(slide_texts):
        image = Image.new("RGB", (1280, 720), "#f7f8fa")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1280, 70), fill="#17212b")
        draw.text((42, 25), f"Slide {index + 1}", fill="#ffffff", font=font)
        wrapped = []
        for paragraph in (text or "(No extractable text)").splitlines():
            while len(paragraph) > 92:
                wrapped.append(paragraph[:92])
                paragraph = paragraph[92:]
            wrapped.append(paragraph)
        draw.multiline_text((56, 110), "\n".join(wrapped[:22]), fill="#24313d", font=font, spacing=12)
        draw.text((56, 676), "Text preview: use LibreOffice or PowerPoint for visual-fidelity rendering.", fill="#687684", font=font)
        destination = output_dir / f"page_{index + 1:03d}.png"
        image.save(destination)
        pages.append(relative_posix(destination, run_dir))
    return RenderedDeck(
        artifact_path=relative_posix(source, run_dir),
        kind="pptx",
        pages=pages,
        page_count=len(pages),
        status="rendered",
        renderer="pptx-text-preview",
    )


def render_artifact(artifact: dict[str, Any], run_dir: Path, output_dir: Path) -> RenderedDeck:
    source = run_dir / artifact["staged_path"]
    kind = artifact["kind"]
    try:
        if kind == "html":
            result = render_html(source, output_dir, run_dir)
        elif kind == "image":
            result = render_image(source, output_dir, run_dir)
        elif kind == "pdf":
            result = render_pdf(source, output_dir, run_dir)
        elif kind == "pptx":
            result = render_pptx_preview(source, output_dir, run_dir)
        else:
            raise RenderError(f"No renderer is registered for artifact kind '{kind}'.")
    except (OSError, RenderError, subprocess.SubprocessError) as exc:
        result = RenderedDeck(
            artifact_path=relative_posix(source, run_dir),
            kind=kind,
            status="failed",
            renderer="",
            error=str(exc),
        )
    write_json(output_dir / "deck.json", result.__dict__ if hasattr(result, "__dict__") else {
        "artifact_path": result.artifact_path,
        "kind": result.kind,
        "pages": result.pages,
        "page_count": result.page_count,
        "status": result.status,
        "renderer": result.renderer,
        "error": result.error,
    })
    return result
