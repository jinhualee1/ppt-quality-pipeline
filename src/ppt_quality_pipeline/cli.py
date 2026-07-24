from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
from pathlib import Path

from . import __version__
from .exporter import export_csv, export_json_summary, export_xlsx
from .pipeline import Pipeline
from .renderers import libreoffice_executable, pdftoppm_available, powerpoint_available
from .server import serve


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_command(args: argparse.Namespace) -> int:
    report = Pipeline().run(
        Path(args.tasks),
        Path(args.output),
        overwrite=args.overwrite,
        render=not args.skip_render,
    )
    summary = report["summary"]
    print(
        f"Completed {summary['items']} items: {summary['passed']} passed, "
        f"{summary['needs_review']} need review, {summary['rendered_pages']} pages rendered."
    )
    print(f"Report: {Path(args.output).resolve() / 'report.json'}")
    return 0


def _demo_command(args: argparse.Namespace) -> int:
    tasks = project_root() / "examples" / "demo" / "tasks.jsonl"
    output = Path(args.output)
    namespace = argparse.Namespace(
        tasks=str(tasks),
        output=str(output),
        overwrite=args.overwrite,
        skip_render=False,
    )
    result = _run_command(namespace)
    try:
        xlsx = export_xlsx(output.resolve())
        print(f"Excel report: {xlsx}")
    except RuntimeError as exc:
        print(f"Excel report skipped: {exc}")
    print(f'Review: pqp serve --run-dir "{output.resolve()}"')
    return result


def _serve_command(args: argparse.Namespace) -> int:
    serve(Path(args.run_dir), args.host, args.port)
    return 0


def _export_command(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    exporters = {
        "csv": export_csv,
        "json": export_json_summary,
        "xlsx": export_xlsx,
    }
    output = Path(args.output).resolve() if args.output else None
    result = exporters[args.format](run_dir, output)
    print(f"Exported: {result}")
    return 0


def _doctor_command(_: argparse.Namespace) -> int:
    checks = {
        "python": True,
        "node": bool(os.environ.get("PQP_NODE") or shutil.which("node")),
        "playwright_core": (project_root() / "node_modules" / "playwright-core").is_dir()
        or bool(os.environ.get("PQP_PLAYWRIGHT_PATH")),
        "chrome": bool(os.environ.get("PQP_CHROME"))
        or any(
            Path(path).is_file()
            for path in [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ]
        ),
        "openpyxl": importlib.util.find_spec("openpyxl") is not None,
        "pillow": importlib.util.find_spec("PIL") is not None,
        "pymupdf": importlib.util.find_spec("fitz") is not None,
        "powerpoint": powerpoint_available(),
        "libreoffice": bool(libreoffice_executable()),
        "pdftoppm": pdftoppm_available(),
    }
    width = max(len(key) for key in checks)
    for key, available in checks.items():
        print(f"{key.ljust(width)}  {'ok' if available else 'not found'}")
    required = ["python", "node", "playwright_core", "chrome"]
    return 0 if all(checks[key] for key in required) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pqp",
        description="Collect, render, evaluate, review, and export presentation quality evidence.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a task file through the pipeline.")
    run_parser.add_argument("--tasks", required=True, help="JSON or JSONL task file.")
    run_parser.add_argument("--output", required=True, help="Run output directory.")
    run_parser.add_argument("--overwrite", action="store_true", help="Replace an existing marked run.")
    run_parser.add_argument(
        "--skip-render", action="store_true", help="Collect and evaluate without rendering."
    )
    run_parser.set_defaults(handler=_run_command)

    demo_parser = subparsers.add_parser("demo", help="Run the synthetic portfolio demo.")
    demo_parser.add_argument("--output", default="runs/demo", help="Demo output directory.")
    demo_parser.add_argument("--overwrite", action="store_true", help="Replace an existing marked demo run.")
    demo_parser.set_defaults(handler=_demo_command)

    serve_parser = subparsers.add_parser("serve", help="Open the human review workspace.")
    serve_parser.add_argument("--run-dir", required=True, help="Completed run directory.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.set_defaults(handler=_serve_command)

    export_parser = subparsers.add_parser("export", help="Export a completed run.")
    export_parser.add_argument("--run-dir", required=True)
    export_parser.add_argument("--format", choices=["csv", "json", "xlsx"], default="xlsx")
    export_parser.add_argument("--output")
    export_parser.set_defaults(handler=_export_command)

    doctor_parser = subparsers.add_parser("doctor", help="Check optional runtime capabilities.")
    doctor_parser.set_defaults(handler=_doctor_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))
