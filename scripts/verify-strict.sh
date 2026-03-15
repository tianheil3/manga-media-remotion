#!/usr/bin/env bash

set -uo pipefail

readonly DEFAULT_COMMANDS_TEXT=$(cat <<'EOF'
python -m pytest apps/api/tests apps/cli/tests tests/bootstrap tests/docs tests/scripts -v
npm test --workspace packages/schema
npm test --workspace apps/web
npm test --workspace apps/remotion
EOF
)

load_commands() {
  local text="$1"
  local -n output_ref="$2"

  output_ref=()
  while IFS= read -r line; do
    if [[ -n "$line" ]]; then
      output_ref+=("$line")
    fi
  done <<< "$text"
}

main() {
  local command_text="${STRICT_VALIDATION_COMMANDS:-$DEFAULT_COMMANDS_TEXT}"
  local extra_text="${STRICT_VALIDATION_EXTRA_COMMANDS:-}"
  local -a commands=()
  local -a extra_commands=()
  local command=""
  local status=0

  load_commands "$command_text" commands
  load_commands "$extra_text" extra_commands
  commands+=("${extra_commands[@]}")

  if [[ "${1:-}" == "--print-commands" ]]; then
    printf '%s\n' "${commands[@]}"
    return 0
  fi

  for command in "${commands[@]}"; do
    printf 'Running strict validation: %s\n' "$command"
    bash -lc "$command"
    status=$?
    if [[ $status -ne 0 ]]; then
      printf 'Strict validation failed: %s\n' "$command" >&2
      return "$status"
    fi
  done

  printf 'Strict validation passed\n'
}

main "$@"
