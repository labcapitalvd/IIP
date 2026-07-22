#!/bin/sh
set -e

# AUTH PORT
: "${PORT_AUTH:?Environment variable PORT_AUTH is required}"

# If validation passes, run the CMD
exec "$@"
