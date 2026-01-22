#!/usr/bin/env bash

if [[ "$1" == "cachebuster" ]]; then
    CACHEBUST=$(date +%s)
    shift
else
    CACHEBUST=1
fi

cd ./Persistence && docker compose build --build-arg CACHEBUST=$CACHEBUST "$@"
cd ./Core && docker compose build --build-arg CACHEBUST=$CACHEBUST "$@"
cd ./IA-Agent && docker compose build --build-arg CACHEBUST=$CACHEBUST "$@"
cd ./Stats && docker compose --profile prod build --build-arg CACHEBUST=$CACHEBUST "$@"
