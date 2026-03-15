# Translation Environment

The CLI translation stage reads its provider configuration from environment variables.

Required variables for the current DeepL provider:

```bash
export TRANSLATION_PROVIDER="deepl"
export DEEPL_API_KEY="your-deepl-api-key"
```

Optional variable:

```bash
export DEEPL_BASE_URL="https://api-free.deepl.com/v2/translate"
```

`apps/cli/app/services/translation_service.py` reads these values when `translate` resolves the default translation provider.

If the required values are missing, the translation stage fails fast with a configuration error instead of writing passthrough or partial script output.

`python -m apps.cli.app.main doctor` runs the same translation setup validation and reports unsupported providers or missing DeepL variables before unattended runs start.
