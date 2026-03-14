#!/usr/bin/env bash

set -uo pipefail

fail() {
  local message="$1"
  local status="${2:-1}"

  printf 'LAND_STATUS=failed\n' >&2
  printf '%s\n' "$message" >&2
  return "$status"
}

default_commit_message() {
  local work_branch="$1"

  if [[ "$work_branch" =~ ([A-Za-z]+-[0-9]+) ]]; then
    printf '%s: land changes\n' "${BASH_REMATCH[1]^^}"
    return 0
  fi

  printf 'land: %s\n' "${work_branch##*/}"
}

run_git() {
  local message="$1"
  shift

  git "$@"
  local status=$?
  if [[ $status -ne 0 ]]; then
    fail "$message" "$status"
    return "$status"
  fi
}

main() {
  local target_branch="${LAND_TARGET_BRANCH:-main}"
  local verify_script="${VERIFY_STRICT_SCRIPT:-scripts/verify-strict.sh}"
  local requested_branch="${1:-}"
  local current_branch=""
  local work_branch=""
  local commit_message=""
  local status=0

  current_branch="$(git branch --show-current)"
  work_branch="$requested_branch"
  if [[ -z "$work_branch" ]]; then
    work_branch="$current_branch"
  fi

  if [[ -z "$work_branch" || "$work_branch" == "$target_branch" ]]; then
    fail "Refusing to land without a non-${target_branch} work branch" 1
    return 1
  fi

  if [[ "$current_branch" != "$work_branch" ]]; then
    run_git "Failed to check out work branch ${work_branch}" checkout "$work_branch" || return $?
  fi

  if [[ ! -x "$verify_script" ]]; then
    fail "Strict verification script is missing or not executable: ${verify_script}" 1
    return 1
  fi

  "$verify_script"
  status=$?
  if [[ $status -ne 0 ]]; then
    fail "Strict validation failed for ${work_branch}" "$status"
    return "$status"
  fi

  run_git "Failed to fetch origin/${target_branch}" fetch origin "$target_branch" || return $?
  run_git "Failed to check out ${target_branch}" checkout "$target_branch" || return $?
  run_git "Failed to reset ${target_branch} to origin/${target_branch}" reset --hard "origin/${target_branch}" || return $?
  run_git "Failed to squash-merge ${work_branch} into ${target_branch}" merge --squash "$work_branch" || return $?

  if git diff --cached --quiet; then
    fail "No staged changes were produced when landing ${work_branch}" 1
    return 1
  fi

  commit_message="${LAND_COMMIT_MESSAGE:-$(default_commit_message "$work_branch")}"
  run_git "Failed to create the squash commit for ${work_branch}" commit -m "$commit_message" || return $?
  run_git "Failed to push ${target_branch} to origin" push origin "$target_branch" || return $?

  printf 'LAND_STATUS=success\n'
  printf 'Landed %s into %s\n' "$work_branch" "$target_branch"
}

main "$@"
