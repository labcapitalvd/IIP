# =================================================
# Stage 1: Start application
# =================================================
FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y \
    gcc\
    g++\
    libpq-dev\
    curl\
    jq\
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 3. Install the packages
# -----------------------------
ARG SHARED=1
WORKDIR /packages
COPY Packages/ ./
RUN pip install --no-cache-dir \
    ./shared_db \
    ./shared_enums \
    ./shared_models \
    ./shared_schemas \
    ./shared_utils
