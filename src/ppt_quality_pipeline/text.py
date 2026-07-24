from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_html_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    return normalize_text(html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def extract_pptx_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        slide_names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        for name in slide_names:
            xml = archive.read(name).decode("utf-8", errors="ignore")
            chunks.extend(html.unescape(item) for item in re.findall(r"<a:t>(.*?)</a:t>", xml, re.DOTALL))
    return normalize_text(" ".join(chunks))


def extract_text(path: Path, kind: str) -> str:
    if kind == "html":
        return extract_html_text(path)
    if kind == "pptx":
        return extract_pptx_text(path)
    if kind in {"file", "text"} and path.suffix.lower() in {".txt", ".md"}:
        return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
    return ""
