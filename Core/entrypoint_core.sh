#!/bin/sh
set -e

# CORE PORT
: "${PORT_CORE:?Environment variable PORT_CORE is required}"

# If validation passes, run the CMD
exec "$@"
