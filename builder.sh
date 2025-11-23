#!/usr/bin/env bash

NO_CACHE_FLAG="${1:-}"
cd ../IIP-Persistence && docker compose build $NO_CACHE_FLAG
cd ../IIP-Auth && docker compose build $NO_CACHE_FLAG
cd ../IIP-Core && docker compose build $NO_CACHE_FLAG
cd ../IIP-IA-Agent && docker compose build $NO_CACHE_FLAG
# cd ../IIP-Stats && docker compose --profile prod build $NO_CACHE_FLAG