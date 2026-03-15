#!/usr/bin/env bash

set -euo pipefail

python -m pytest tests/e2e/test_sample_project_smoke.py -v "$@"
