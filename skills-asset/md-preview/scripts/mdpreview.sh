#!/usr/bin/env bash
# Use an explicitly prepared Python environment; no implicit downloads or shared /tmp venv.
set -euo pipefail
exec python3 "$(dirname "$0")/mdpreview.py" "$@"
