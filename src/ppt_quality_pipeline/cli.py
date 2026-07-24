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
        f"已完成 {summary['items']} 个任务：{summary['passed']} 个通过，"
        f"{summary['needs_review']} 个待复核，共渲染 {summary['rendered_pages']} 页。"
    )
    print(f"报告：{Path(args.output).resolve() / 'report.json'}")
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
        print(f"Excel 报告：{xlsx}")
    except RuntimeError as exc:
        print(f"已跳过 Excel 报告：{exc}")
    print(f'打开标注工作台：pqp serve --run-dir "{output.resolve()}"')
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
    print(f"已导出：{result}")
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
        print(f"{key.ljust(width)}  {'可用' if available else '未找到'}")
    required = ["python", "node", "playwright_core", "chrome"]
    return 0 if all(checks[key] for key in required) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pqp",
        description="采集、渲染、评估、复核并导出演示文稿质量证据。",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="运行任务文件。")
    run_parser.add_argument("--tasks", required=True, help="JSON 或 JSONL 任务文件。")
    run_parser.add_argument("--output", required=True, help="运行结果输出目录。")
    run_parser.add_argument("--overwrite", action="store_true", help="覆盖已有且带标记的运行目录。")
    run_parser.add_argument("--skip-render", action="store_true", help="只采集和评估，不进行页面渲染。")
    run_parser.set_defaults(handler=_run_command)

    demo_parser = subparsers.add_parser("demo", help="运行中文合成演示。")
    demo_parser.add_argument("--output", default="runs/demo", help="演示结果输出目录。")
    demo_parser.add_argument("--overwrite", action="store_true", help="覆盖已有且带标记的演示目录。")
    demo_parser.set_defaults(handler=_demo_command)

    serve_parser = subparsers.add_parser("serve", help="打开人工标注工作台。")
    serve_parser.add_argument("--run-dir", required=True, help="已完成的运行目录。")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.set_defaults(handler=_serve_command)

    export_parser = subparsers.add_parser("export", help="导出已完成的运行结果。")
    export_parser.add_argument("--run-dir", required=True)
    export_parser.add_argument("--format", choices=["csv", "json", "xlsx"], default="xlsx")
    export_parser.add_argument("--output")
    export_parser.set_defaults(handler=_export_command)

    doctor_parser = subparsers.add_parser("doctor", help="检查可选运行能力。")
    doctor_parser.set_defaults(handler=_doctor_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))
