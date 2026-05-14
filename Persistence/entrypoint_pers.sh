#!/bin/sh
set -e

# MODE
: "${PRODUCTION_MODE:?Environment variable PRODUCTION_MODE is required}"
: "${LOGLEVEL:?Environment variable LOGLEVEL is required}"

# DB
: "${POSTGRES_USER:?Environment variable POSTGRES_USER is required}"
: "${POSTGRES_DB:?Environment variable POSTGRES_DB is required}"

# POPS
: "${HOST_AUTH:?Environment variable HOST_AUTH is required}"
: "${PORT_AUTH:?Environment variable PORT_AUTH is required}"
: "${HOST_CORE:?Environment variable HOST_CORE is required}"
: "${PORT_CORE:?Environment variable PORT_CORE is required}"

# If validation passes, run the CMD
exec "$@"
