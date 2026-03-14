# Moyin Environment

The TTS integration reads its runtime configuration from environment variables.

Required variables:

```bash
export MOYIN_TTS_BASE_URL="https://your-moyin-endpoint.example/tts"
export MOYIN_TTS_API_KEY="your-api-key"
```

The CLI voice stage uses these values when `apps/cli/app/services/voice_generation.py` creates the default Moyin provider.

If these values are missing, the voice stage will fail fast with a configuration error instead of silently generating incorrect audio.
