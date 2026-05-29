#!/bin/sh
set -e

# MODE
: "${PRODUCTION_MODE:?Environment variable PRODUCTION_MODE is required}"
: "${LOGLEVEL:?Environment variable LOGLEVEL is required}"

# DB
: "${POSTGRES_USER:?Environment variable POSTGRES_USER is required}"
: "${POSTGRES_DB:?Environment variable POSTGRES_DB is required}"

# TOKENS
: "${JWT_EXPIRE_MINUTES_ACCESS:?Environment variable JWT_EXPIRE_MINUTES_ACCESS is required}"
: "${JWT_EXPIRE_MINUTES_REFRESH:?Environment variable JWT_EXPIRE_MINUTES_REFRESH is required}"

# If validation passes, run the CMD
exec "$@"
