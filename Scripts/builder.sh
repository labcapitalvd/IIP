#!/usr/bin/env bash

if [[ "$1" == "shared" ]]; then
  SHARED=$(date +%s)
  shift
else
  SHARED=1
fi

if [[ "$1" == "applications" ]]; then
  APPLICATION=$(date +%s)
  shift
else
  APPLICATION=1
fi

(
  docker compose -f ../compose.yaml build \
    --build-arg SHARED="$SHARED" "$@" \
    --build-arg APPLICATION="$APPLICATION" "$@"
)
