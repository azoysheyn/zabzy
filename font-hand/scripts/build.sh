#!/bin/sh
# Build Zabzy Hand. The first run makes .venv and installs the tools.
set -eu
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip -q install fonttools svgpathtools brotli uharfbuzz picosvg
fi
.venv/bin/python scripts/build_font.py
.venv/bin/python scripts/check_shaping.py
.venv/bin/python scripts/kerning_table.py
