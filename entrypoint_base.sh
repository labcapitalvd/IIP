#!/bin/sh
set -e

# CORS DIRECT API
: "${PUBLIC_ORIGINS:?Environment variable PUBLIC_ORIGINS is required}"

# CORS FRONTEND ONLY
: "${PRIVATE_ORIGINS:?Environment variable PRIVATE_ORIGINS is required}"

# If validation passes, run the CMD
exec "$@"
