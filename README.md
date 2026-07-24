# PPT Quality Pipeline

A reproducible toolkit for collecting presentation artifacts, rendering slides,
checking explicit requirements, conducting human visual review, and exporting
evidence-backed quality reports.

[中文说明](README.zh-CN.md)

![PPT Quality Review workspace](docs/images/review-workspace.png)

## Why this project

Presentation evaluation often mixes file collection, rendering, subjective
review, and spreadsheet updates in one-off scripts. PPT Quality Pipeline turns
that work into a traceable run:

```text
Task JSONL -> staged artifacts -> rendered pages -> automated issues
           -> human annotations -> JSON / CSV / XLSX reports
```

The public repository uses synthetic fixtures only. Source-specific collectors
can stay private while sharing the same normalized pipeline.

## Features

- Deterministic run archives with provenance for every artifact
- HTML slide rendering through Playwright and system Chrome/Chromium
- Image, PDF, and portable PPTX preview adapters
- Page-count, required-content, forbidden-content, and missing-output checks
- Local human-review workspace for overflow, overlap, blank pages, and notes
- JSON, CSV, and optional XLSX exports
- Safe overwrite markers and path traversal protection
- Synthetic pass/fail demo and dependency-light unit tests

## Quick start

Requirements:

- Python 3.10+
- Node.js 20+
- Chrome, Edge, or Chromium

```bash
git clone https://github.com/your-name/ppt-quality-pipeline.git
cd ppt-quality-pipeline

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

python -m pip install -e ".[xlsx,pptx]"
corepack enable
pnpm install

pqp doctor
pqp demo
pqp serve --run-dir runs/demo
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765) to review the rendered
slides. The demo produces one passing item and one item with intentional
page-count and content findings.

## Run your own tasks

Create a JSONL task file:

```json
{"id":"deck-001","query":"Create a three-slide review deck.","artifacts":[{"path":"deck.html","kind":"html","role":"generated"}],"expectation":{"page_count":3,"required_keywords":["evidence","review"]}}
```

Then run:

```bash
pqp run --tasks tasks.jsonl --output runs/my-run
pqp serve --run-dir runs/my-run
pqp export --run-dir runs/my-run --format xlsx
```

See [Task format](docs/task-format.md) for the full schema.

## Project structure

```text
src/ppt_quality_pipeline/
  collector.py      local artifact staging
  renderers.py      HTML, image, PDF, and PPTX adapters
  evaluator.py      deterministic requirement checks
  server.py         local annotation API
  exporter.py       JSON, CSV, and XLSX reports
  web/              human-review interface
examples/demo/      synthetic presentation fixtures
scripts/            browser rendering helper
tests/              dependency-light unit tests
docs/               architecture and data contracts
```

## Rendering support

| Input | Support | Notes |
| --- | --- | --- |
| HTML | Full | Playwright captures `[data-slide]`, `.slide`, `.ppt-slide`, or `section`. |
| Images | Full | Each image is treated as one rendered page. |
| PDF | Optional | Install the `pdf` extra for PyMuPDF rendering. |
| PPTX | Preview | Extracts slide text into portable previews; use a production adapter for visual fidelity. |

The renderer registry is intentionally replaceable. A deployment can add
LibreOffice, Microsoft PowerPoint, or a managed rendering service without
changing the evaluator or review workspace.

## Architecture and safety

- [Architecture](docs/architecture.md)
- [Task data contract](docs/task-format.md)
- [Security and data handling](SECURITY.md)
- [Portfolio notes](docs/portfolio.md)

Never commit browser profiles, collected user files, internal endpoints, or
private evaluation data. The review server is local-only and has no
authentication.

## Development

```bash
python -m unittest discover -s tests -v
pnpm run check
```

GitHub Actions runs both checks on every push and pull request.

## License

MIT
