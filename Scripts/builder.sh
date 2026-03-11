#!/usr/bin/env bash
if [[ "$1" == "installer" ]]; then
  INSTALLER=$(date +%s)
  shift
else
  INSTALLER=1
fi

if [[ "$1" == "shared" ]]; then
  SHARED=$(date +%s)
  shift
else
  SHARED=1
fi

if [[ "$1" == "models" ]]; then
  MODELS=$(date +%s)
  shift
else
  MODELS=1
fi

if [[ "$1" == "applications" ]]; then
  APPLICATION=$(date +%s)
  shift
else
  APPLICATION=1
fi

(
  docker compose -f ../compose.yaml build \
    --build-arg INSTALLER="$INSTALLER" "$@" \
    --build-arg SHARED="$SHARED" "$@" \
    --build-arg MODELS="$MODELS" "$@" \
    --build-arg APPLICATION="$APPLICATION" "$@"
)

