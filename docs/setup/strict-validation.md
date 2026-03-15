# Strict Validation

Repository strict validation is defined by `scripts/verify-strict.sh`.

## Default Command Order

The default strict validation suite runs these commands in order:

1. `python -m pytest apps/api/tests apps/cli/tests tests/bootstrap tests/docs tests/scripts -v`
2. `bash scripts/smoke-sample-project.sh`
3. `npm test --workspace packages/schema`
4. `npm test --workspace apps/web`
5. `npm test --workspace apps/remotion`

The script stops on the first failure and returns that command's exit code.

The smoke step copies the committed fixture at `tests/fixtures/workspace/demo-001/` into a temporary workspace, checks the CLI/API happy path, and renders a preview MP4.

## Issue-Specific Validation

If a Linear issue includes additional `Validation`, `Testing`, or `Test Plan` commands, append them through `STRICT_VALIDATION_EXTRA_COMMANDS` as newline-separated shell commands.

Example:

```bash
export STRICT_VALIDATION_EXTRA_COMMANDS=$'python -m pytest tests/scripts -v\nnpm test --workspace packages/schema'
bash scripts/verify-strict.sh
```

## Inspecting The Effective Command List

Use this to print the final command list without running it:

```bash
bash scripts/verify-strict.sh --print-commands
```
