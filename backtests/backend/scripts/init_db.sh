#!/usr/bin/env bash

set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "=========================================="
echo "   backtests SQLite 初始化"
echo "=========================================="
echo ""

cd "$BACKEND_DIR"
"$PYTHON_BIN" scripts/create_tables.py

echo ""
echo "=========================================="
echo "✅ 初始化完成: ../../.runtime/database/backtests.sqlite3"
echo "=========================================="
echo ""
