# Rendering Backends

The pipeline records both the renderer name and its fidelity level for every
deck. This prevents a text-only preview from being mistaken for visual
evidence.

## PPTX selection order

The default `PQP_PPTX_BACKEND=auto` mode tries:

1. **Microsoft PowerPoint** on Windows
2. **LibreOffice** on Windows, macOS, or Linux
3. **Text preview** as an explicit low-fidelity fallback

Set `PQP_PPTX_STRICT=1` to fail the render instead of accepting the preview.

## Microsoft PowerPoint

The Windows backend opens the source read-only through COM and calls the native
slide export API for every slide. It preserves the rendering behavior of the
installed PowerPoint version, including fonts, theme resolution, shapes,
images, charts, and slide geometry.

Pages are exported as PNG files at 1080 pixels high by default. The width is
calculated from the presentation's native aspect ratio.

```powershell
$env:PQP_PPTX_BACKEND = "powerpoint"
$env:PQP_PPTX_HEIGHT = "1440"
pqp run --tasks tasks.jsonl --output runs/native
```

The helper opens presentations without a visible window, disables macro
automation where supported, releases all COM objects, and always closes
PowerPoint.

## LibreOffice

The cross-platform backend launches LibreOffice in headless mode with an
isolated user profile. It converts PPTX to PDF, then rasterizes the PDF through
PyMuPDF or Poppler.

```bash
export PQP_PPTX_BACKEND=libreoffice
export PQP_LIBREOFFICE=/usr/bin/libreoffice
pqp run --tasks tasks.jsonl --output runs/libreoffice
```

LibreOffice is high fidelity for most decks, but fonts, SmartArt, embedded
media, and some PowerPoint-specific effects can differ from native PowerPoint.

## PDF rasterization

PDF rendering tries:

1. PyMuPDF from the optional `pdf` dependency
2. Poppler `pdftoppm`

Use `PQP_PDFTOPPM` when Poppler is installed outside `PATH`.

## Report contract

Each rendered deck includes:

```json
{
  "renderer": "microsoft-powerpoint",
  "fidelity": "high",
  "page_count": 3,
  "warnings": []
}
```

When only the preview is available, the evaluator emits
`LOW_FIDELITY_RENDER`, and the item is marked for review.
