#!/usr/bin/env bash
cd ../IIP-Persistence && docker compose build "$@"
cd ../IIP-Auth && docker compose build "$@"
cd ../IIP-Core && docker compose build "$@"
cd ../IIP-IA-Agent && docker compose build "$@"
# cd ../IIP-Stats && docker compose --profile prod build "$@"
