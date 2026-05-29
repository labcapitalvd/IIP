#!/bin/sh
set -e

# POPS
: "${HOST_AUTH:?Environment variable HOST_AUTH is required}"
: "${PORT_AUTH:?Environment variable PORT_AUTH is required}"
: "${HOST_CORE:?Environment variable HOST_CORE is required}"
: "${PORT_CORE:?Environment variable PORT_CORE is required}"

# If validation passes, run the CMD
exec "$@"
