#!/usr/bin/env bash

if [[ "$1" == "cachebuster" ]]; then
    CACHEBUST=$(date +%s)
    shift
else
    CACHEBUST=1
fi

cd ./Persistence && docker compose build --build-arg FETCHER=$FETCHER "$@" --build-arg PACKAGES=$PACKAGES "$@"
cd ./Core && docker compose build --build-arg FETCHER=$FETCHER "$@" --build-arg PACKAGES=$PACKAGES "$@"
cd ./IA-Agent && docker compose build --build-arg FETCHER=$FETCHER "$@" --build-arg PACKAGES=$PACKAGES "$@"
cd ./Stats && docker compose --profile prod build --build-arg FETCHER=$FETCHER "$@" --build-arg PACKAGES=$PACKAGES "$@"
