# Translation Environment

The CLI OCR and translation stages read their MIT service configuration from environment variables.

Required variable:

```bash
export MANGA_IMAGE_TRANSLATOR_BASE_URL="http://127.0.0.1:5003"
```

Optional variables:

```bash
export MANGA_IMAGE_TRANSLATOR_OCR_PATH="/translate/with-form/json"
export MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH="/translate/text"
export MANGA_IMAGE_TRANSLATOR_API_KEY="optional-bearer-token"
```

The repository expects one MIT service base URL for both stages:

- `ocr` posts the source image to `MANGA_IMAGE_TRANSLATOR_OCR_PATH`, which defaults to the upstream MIT form JSON endpoint.
- `translate` posts reviewed text to `MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH`, which defaults to `/translate/text`.

If your deployed MIT service is a thin wrapper around the upstream server, expose a text-translation endpoint at `MANGA_IMAGE_TRANSLATOR_TRANSLATE_PATH` that accepts:

```json
{
  "text": "cleaned japanese",
  "sourceLanguage": "ja",
  "targetLanguage": "zh"
}
```

and returns JSON containing `translatedText`.

If `MANGA_IMAGE_TRANSLATOR_API_KEY` is set, the CLI sends it as a bearer token to both OCR and translation requests.

If the required values are missing, the OCR and translation stages fail fast with a configuration error instead of mutating workspace outputs.

`python -m apps.cli.app.main doctor` runs the same setup validation and reports missing MIT variables before unattended runs start.
