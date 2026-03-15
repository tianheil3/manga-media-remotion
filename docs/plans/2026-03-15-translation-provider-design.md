# Translation Provider Design

**Date:** 2026-03-15

**Status:** Approved for implementation in unattended issue execution

## Context

`TIA-22` replaces the current passthrough translation stage with a provider-backed implementation while preserving the existing local-first script workflow. The approved workflow design already requires separate OCR, reviewed, translated, voice, and subtitle layers, so this ticket should stay narrowly focused on the translation stage and should not change downstream voice or scene logic.

## Requirements

- The `translate` command must use a real provider client instead of returning source text unchanged.
- Provider credentials and configuration must come from environment variables.
- Translation failures must stop the command with an actionable message.
- Existing project data must not be corrupted if translation fails partway through a run.
- Local overrides for `translatedText`, `voiceText`, and `subtitleText` must continue to win over provider output.

## Approaches Considered

### 1. Single-provider client with env-selected factory

Implement one real provider client now, selected through `TRANSLATION_PROVIDER`, with provider-specific credentials loaded from the environment.

Pros:

- Smallest change that satisfies the ticket.
- Keeps the public translation interface stable.
- Easy to test with injected transport functions.

Cons:

- Only one provider is available initially.

### 2. Full provider registry with multiple backends now

Add a generic registry and implement several providers immediately.

Pros:

- More extensible up front.

Cons:

- Larger surface area and more configuration complexity than the ticket requires.
- Higher risk of untested branches in the MVP pipeline.

### 3. Project-configured provider settings stored under `workspace/<project-id>/`

Store provider choice and credentials in project-local config files.

Pros:

- Per-project configuration flexibility.

Cons:

- Conflicts with the ticket requirement that credentials come from environment variables.
- Risks persisting secrets into local project data.

## Recommendation

Choose approach 1. Add a single real translation provider client now and keep provider selection behind the existing `TranslationService` interface. This gives the CLI a real external provider without overbuilding provider management.

## Selected Provider

Use DeepL for the first provider-backed implementation.

Why:

- It is a translation-specific provider rather than a generic text model.
- It can be integrated with the Python standard library `urllib` stack already used elsewhere in the repo.
- The environment contract is simple: `TRANSLATION_PROVIDER=deepl`, `DEEPL_API_KEY`, and optional `DEEPL_BASE_URL`.

## Design

### Service Layer

- Keep `TranslationService` as the protocol used by `script_builder`.
- Replace `PassthroughTranslationService` as the default factory result with a `DeepLTranslationService`.
- Add a typed `TranslationServiceError` for unsupported or misconfigured providers and provider request failures.
- Load provider configuration from environment variables in `get_translation_service()`.

### Translation Flow

- `translate` command resolves the provider from env before calling `run_translation`.
- `build_script_entries()` translates each reviewed bubble in memory.
- After provider output is returned, apply overrides in this order:
  - `translatedText`
  - `voiceText`
  - `subtitleText`
- Persist `script/script.json` only after all entries are built successfully.

### Failure Handling

- If the provider is missing configuration, fail with an actionable message naming the required environment variables.
- If a provider request fails, wrap the error with frame and bubble identifiers so the user knows what failed.
- Do not write partial script output on failure. Existing `script.json` must remain unchanged.

### Testing

- Successful translation path with a fake provider.
- Override precedence, including `translatedText` override winning over provider output.
- Provider failure path proving the CLI exits with a clear error and existing script data is preserved.
- Provider env-loading tests for configured and misconfigured states.
