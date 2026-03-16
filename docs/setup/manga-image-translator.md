# Manga Image Translator Service

The CLI no longer runs local `manga-ocr` or DeepL. Both `ocr` and `translate` call an external manga-image-translator (MIT) service instead.

## Required Setup

Export the MIT base URL before running the CLI stages that depend on OCR or translation:

```bash
export MANGA_IMAGE_TRANSLATOR_BASE_URL="http://127.0.0.1:5003"
```

Optional overrides:

```bash
export MANGA_IMAGE_TRANSLATOR_OCR_PATH="/translate/with-form/json"
export MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH="/translate/text"
export MANGA_IMAGE_TRANSLATOR_API_KEY="optional-bearer-token"
```

If `MANGA_IMAGE_TRANSLATOR_API_KEY` is set, the CLI sends it as a bearer token on both OCR and translation requests.

## Endpoint Contract

The repository uses two MIT-facing calls:

- OCR: `ocr` posts each frame image to `MANGA_IMAGE_TRANSLATOR_OCR_PATH`. The default is the upstream MIT form JSON endpoint, `translate/with-form/json`.
- Translation: `translate` posts reviewed text to `MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH`. The default is `/translate/text` so reviewed source text remains authoritative after the review step.

The OCR endpoint should return either the upstream MIT `translations` payload or a simplified `bubbles` payload. The CLI converts that response into the existing `ocr/*.json` bubble format and updates `script/frames.json` without changing the downstream workspace contract.

The text-translation endpoint should accept:

```json
{
  "text": "cleaned japanese",
  "sourceLanguage": "ja",
  "targetLanguage": "zh"
}
```

and return JSON containing `translatedText`.

## Verification

Run the shared setup check after exporting the MIT variables:

```bash
python -m apps.cli.app.main doctor
```

Expected MIT-related lines:

```text
OK OCR manga-image-translator
OK translation manga-image-translator
```

If your deployment is a thin wrapper around the upstream MIT server, keep the default OCR path and add a small text-translation endpoint at `/translate/text` (or override `MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH` to match your wrapper).
