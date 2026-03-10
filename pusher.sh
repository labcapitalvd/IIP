#!/usr/bin/env bash
(
  docker push labcapital/apps:IIP-Persister
)

(
  docker push labcapital/apps:IIP-Core
)

(
  docker push labcapital/apps:IIP-IA-Agent
)

(
  docker push labcapital/apps:IIP-Stats
)
