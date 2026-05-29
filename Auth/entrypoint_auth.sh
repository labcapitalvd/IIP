#!/bin/sh
set -e

# PORT API
: "${PORT_AUTH:?Environment variable PORT_AUTH is required}"

# If validation passes, run the CMD
exec "$@"
