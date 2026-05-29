#!/bin/sh
set -e

# PORT API
: "${PORT_AUTH:?Environment variable PORT_AUTH is required}"

# CORS DIRECT API
: "${PUBLIC_ORIGINS:?Environment variable PUBLIC_ORIGINS is required}"

# CORS FRONTEND ONLY
: "${PRIVATE_ORIGINS:?Environment variable PRIVATE_ORIGINS is required}"

# TOKENS
: "${JWT_EXPIRE_MINUTES_ACCESS:?Environment variable JWT_EXPIRE_MINUTES_ACCESS is required}"
: "${JWT_EXPIRE_MINUTES_REFRESH:?Environment variable JWT_EXPIRE_MINUTES_REFRESH is required}"

# If validation passes, run the CMD
exec "$@"
