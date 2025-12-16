#!/usr/bin/env bash
set -e

# MODE
: "${PRODUCTION_MODE:?Environment variable PRODUCTION_MODE is required}"
: "${LOGLEVEL:?Environment variable LOGLEVEL is required}"

# DB
: "${POSTGRES_USER:?Environment variable POSTGRES_USER is required}"
: "${POSTGRES_DB:?Environment variable POSTGRES_DB is required}"

# PORT API
: "${PORT_CORE:?Environment variable PORT_CORE is required}"

# CORS DIRECT API
: "${PUBLIC_ORIGINS:?Environment variable PUBLIC_ORIGINS is required}"

# CORS FRONTEND ONLY
: "${NODE_ORIGINS:?Environment variable NODE_ORIGINS is required}"

# echo "================================================="
# echo "  DIAGNOSTIC: PYTHON ENVIRONMENT CHECK"
# echo "================================================="
# echo "Using interpreter: $(which python)"
# python -c 'import sys; from pprint import pprint; pprint(sys.path)'

# ls /api


# If validation passes, run the CMD
exec "$@"