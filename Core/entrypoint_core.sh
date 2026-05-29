#!/bin/sh
set -e

# PORT API
: "${PORT_CORE:?Environment variable PORT_CORE is required}"

# If validation passes, run the CMD
exec "$@"
