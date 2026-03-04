#!/usr/bin/env bash
set -e

# Usage: fetch.sh <github_repo> <filename>
# Example: ./fetch.sh LABCapital-VD/Commons shared_db.zip

FILENAME="$1"

if [ -z "$FILENAME" ]; then
  echo "❌ Error: No FILENAME provided."
  exit 1
fi

echo "Installing $FILENAME..."
# Install if Python package
pip install "$FILENAME" --no-cache-dir --force-reinstall
