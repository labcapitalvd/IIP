# =================================================
# Stage 1: Start application
# =================================================
FROM python:3.14-slim-bookworm
RUN apt-get update && apt-get install -y \
    gcc\
    g++\
    libpq-dev\
    curl\
    jq\
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 2. Get the installer
# -----------------------------
ARG INSTALLER=1
COPY Packages/installer.sh /installer.sh
RUN chmod +x /installer.sh

# -----------------------------
# 3. Install the packages
# -----------------------------
WORKDIR /packages
ARG SHARED=1
COPY Packages/shared_db .
COPY Packages/shared_models .
COPY Packages/shared_schemas .
COPY Packages/shared_utils .
RUN \
    /installer.sh shared_db \
    /installer.sh shared_models \
    /installer.sh shared_schemas \
    /installer.sh shared_utils

ARG MODELS=1
COPY Packages/models .
RUN \
    /installer.sh models

COPY src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

# -----------------------------
# 4. Copy app
# -----------------------------
WORKDIR /api
ARG APPLICATION=1
COPY src/migrator ./migrator
COPY src/schemer ./schemer
COPY src/seeder ./seeder

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY entrypoint_pers.sh /entrypoint_pers.sh
RUN chmod +x /entrypoint_pers.sh
ENTRYPOINT ["/entrypoint_pers.sh"]
