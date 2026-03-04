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

COPY Packages/shared_db ./shared_db
COPY Packages/shared_models ./shared_models
COPY Packages/shared_schemas ./shared_schemas
COPY Packages/shared_utils ./shared_utils
COPY Persistence/src/models ./models
RUN pip install --no-cache-dir /packages/shared_db
RUN pip install --no-cache-dir /packages/shared_models
RUN pip install --no-cache-dir /packages/shared_schemas
RUN pip install --no-cache-dir /packages/shared_utils
RUN pip install --no-cache-dir /packages/models

# -----------------------------
# 4. Copy app
# -----------------------------
ARG APPLICATION=1
WORKDIR /api

COPY Persistence/src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY Persistence/src/migrator ./migrator
COPY Persistence/src/schemer ./schemer
COPY Persistence/src/seeder ./seeder

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Persistence/entrypoint_pers.sh /entrypoint_pers.sh
RUN chmod +x /entrypoint_pers.sh
ENTRYPOINT ["/entrypoint_pers.sh"]
