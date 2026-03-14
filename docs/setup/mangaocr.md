# MangaOCR Setup

OCR execution depends on the `manga-ocr` Python package being available in the active environment.

Example installation:

```bash
pip install manga-ocr
```

After installation, verify the package is importable in the same environment that runs the CLI:

```bash
python - <<'PY'
from manga_ocr import MangaOcr
print(MangaOcr)
PY
```

The CLI OCR stage lazily imports `manga-ocr`, so projects can still use non-OCR stages even when the package has not been installed yet.
