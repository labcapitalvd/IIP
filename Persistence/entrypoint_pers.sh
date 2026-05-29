#!/bin/sh
set -e

# POPS
: "${PORT_AUTH:?Environment variable PORT_AUTH is required}"
: "${PORT_CORE:?Environment variable PORT_CORE is required}"

# If validation passes, run the CMD
exec "$@"
