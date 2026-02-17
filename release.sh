#!/usr/bin/env bash

# Exit immediately if a command fails
set -e

# 1. Check if a version argument was provided (e.g., ./release.sh v1.2.4)
if [ -z "$1" ]; then
    echo "❌ Error: No version provided."
    echo "Usage: ./release.sh v1.x.x"
    exit 1
fi

VERSION=$1

# 2. Setup a temporary workspace
TMP_DIR=$(mktemp -d -t release-XXXXXX)
echo "📦 Working in temporary directory: $TMP_DIR"

# Ensure cleanup happens even if the script crashes or you Ctrl+C
trap 'rm -rf "$TMP_DIR"; echo "🧹 Cleaned up $TMP_DIR"' EXIT

# 3. Create the zips inside the tmp directory
echo "🗜️  Zipping packages..."
(cd Persistence/src/models && zip -rq "$TMP_DIR/models.zip" .)

# 4. Verification of Token
if [ -z "$GITHUB_TOKEN_IIP" ]; then
    echo "❌ Error: GITHUB_TOKEN is not set."
    echo "Make sure you ran 'direnv allow' or have the secret in your env."
    exit 1
fi

# 5. Run ghr to upload to GitHub
echo "🚀 Uploading $VERSION to GitHub..."
ghr -t "$GITHUB_TOKEN_IIP" \
    -u LABCapital-IIP \
    -r IIP \
    -replace \
    "$VERSION" "$TMP_DIR/"

echo "✅ Release $VERSION successful!"













