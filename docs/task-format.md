# Task Format

Tasks are supplied as JSON or JSONL. Paths are resolved relative to the task
file.

```json
{
  "id": "example-001",
  "query": "Create a three-slide review deck.",
  "artifacts": [
    {
      "path": "deck.html",
      "kind": "html",
      "role": "generated",
      "label": "Generated deck"
    }
  ],
  "expectation": {
    "page_count": 3,
    "required_keywords": ["evidence", "review"],
    "forbidden_keywords": ["confidential"]
  },
  "metadata": {
    "scenario": "public-demo"
  }
}
```

## Artifact kinds

| Kind | Current behavior |
| --- | --- |
| `html` | Render each `[data-slide]`, `.slide`, `.ppt-slide`, or `section` with Playwright. |
| `image` | Stage the image as a one-page rendered deck. |
| `pdf` | Render pages when the optional PyMuPDF dependency is installed. |
| `pptx` | Produce a text-oriented preview with Pillow and optional `python-pptx`. |
| `auto` | Infer the kind from the file extension. |

`role` should be `generated` for the artifact being evaluated. Other roles can
be used by custom evaluators for references, templates, and attachments.
