#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

export PYINSTALLER_CONFIG_DIR="$ROOT_DIR/.pyinstaller-config"
export XDG_CACHE_HOME="$ROOT_DIR/.cache"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source ".venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install pyinstaller requests beautifulsoup4

rm -rf build dist

python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "Charlie Skill" \
  --add-data "skills/company-filter/data:seed_data" \
  "skills/company-filter-refresh/refresh.py"

echo ""
echo "macOS app created:"
echo "  $ROOT_DIR/dist/Charlie Skill.app"
