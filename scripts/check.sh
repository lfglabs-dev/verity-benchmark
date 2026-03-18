#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 scripts/generate_metadata.py
./scripts/run_all.sh
