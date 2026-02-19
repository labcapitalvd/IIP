#!/usr/bin/env bash
if [[ "$1" == "fetcher" ]]; then
  FETCHER=$(date +%s)
  shift
else
  FETCHER=1
fi

if [[ "$1" == "packages" ]]; then
  PACKAGES=$(date +%s)
  shift
else
  PACKAGES=1
fi

(
  cd Persistence && docker compose build \
    --build-arg FETCHER="$FETCHER" "$@" \
    --build-arg PACKAGES="$PACKAGES" "$@" &&
    docker push labcapital/apps:IIP-Persister
)

(
  cd Core && docker compose build \
    --build-arg FETCHER="$FETCHER" "$@" \
    --build-arg PACKAGES="$PACKAGES" "$@" &&
    docker push labcapital/apps:IIP-Core
)

(
  cd IA-Agent && docker compose build \
    --build-arg FETCHER="$FETCHER" "$@" \
    --build-arg PACKAGES="$PACKAGES" "$@" &&
    docker push labcapital/apps:IIP-IA-Agent
)

(
  cd Stats && docker compose \
    --profile prod build \
    --build-arg FETCHER="$FETCHER" "$@" \
    --build-arg PACKAGES="$PACKAGES" "$@" &&
    docker push labcapital/apps:IIP-Stats
)
