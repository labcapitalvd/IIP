# =================================================
# Stage 1: Isolate Cache Metadata
# =================================================
FROM alpine:latest AS structural-setup
COPY Packages/shared/pyproject.toml /shared/
COPY Packages/shared/src/shared/__init__.py /shared/src/shared/


# =================================================
# Base Dependency Layer
# =================================================
FROM python:3.12-slim-bookworm AS base-env

RUN apt-get update && apt-get install -y \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /packages
COPY --from=structural-setup /shared ./shared
RUN pip install --no-cache-dir ./shared


# =================================================
# Final Application Image
# =================================================
FROM base-env AS final-app
WORKDIR /api

# 1. Cache the App dependencies
COPY Core/src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir . || true

# 2. Drop the REAL code implementations into place 
# (Busts cache from here down—takes less than a second)
COPY Packages/shared/ /packages/shared/
COPY Core/src/ ./

# Re-run fast, local installs without hitting the network to sync source code
RUN pip install --no-cache-dir --no-deps /packages/shared .

COPY Core/entrypoint_core.sh /entrypoint_core.sh
RUN chmod +x /entrypoint_core.sh

ENTRYPOINT ["/entrypoint_core.sh"]
CMD ["sh", "-c", "exec uvicorn main:api --host 0.0.0.0 --port $PORT_CORE"]
