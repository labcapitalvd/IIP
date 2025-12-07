#!/usr/bin/env bash

if [[ "$1" == "cachebuster" ]]; then
    CACHEBUST=$(date +%s)
    shift
else
    CACHEBUST=1
fi

cd ../IIP-Persistence && docker compose build --build-arg CACHEBUST=$CACHEBUST "$@"
cd ../IIP-Core && docker compose build --build-arg CACHEBUST=$CACHEBUST "$@"
cd ../IIP-IA-Agent && docker compose build --build-arg CACHEBUST=$CACHEBUST "$@"
cd ../IIP-Stats && docker compose --profile prod build --build-arg CACHEBUST=$CACHEBUST "$@"
