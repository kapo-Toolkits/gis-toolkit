#!/bin/bash
# macOS / Linux launcher — double-click (macOS) or run: bash GIS_BOX.command
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
    python3 gis_box.py
else
    python gis_box.py
fi
