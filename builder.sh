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
  MODELS=$(date +%s)
  shift
else
  MODELS=1
fi

(
  cd Persistence && docker compose build \
    --build-arg INSTALLER="$INSTALLER" "$@" \
    --build-arg SHARED="$SHARED" "$@" \
    --build-arg MODELS="$MODELS" "$@" \
    --build-arg APPLICATION="$APPLICATION" "$@"
)

(
  cd Core && docker compose build \
    --build-arg INSTALLER="$INSTALLER" "$@" \
    --build-arg SHARED="$SHARED" "$@" \
    --build-arg MODELS="$MODELS" "$@" \
    --build-arg APPLICATION="$APPLICATION" "$@"
)

(
  cd IA-Agent && docker compose build \
    --build-arg INSTALLER="$INSTALLER" "$@" \
    --build-arg SHARED="$SHARED" "$@" \
    --build-arg MODELS="$MODELS" "$@" \
    --build-arg APPLICATION="$APPLICATION" "$@"
)

(
  cd Stats && docker compose \
    --profile prod build \
    --build-arg INSTALLER="$INSTALLER" "$@" \
    --build-arg SHARED="$SHARED" "$@" \
    --build-arg MODELS="$MODELS" "$@" \
    --build-arg APPLICATION="$APPLICATION" "$@"
)
