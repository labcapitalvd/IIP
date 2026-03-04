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
ARG SHARED=1
WORKDIR /packages

COPY Packages/shared_db ./shared_db
COPY Packages/shared_models ./shared_models
COPY Packages/shared_schemas ./shared_schemas
COPY Packages/shared_utils ./shared_utils
COPY Persistence/src/models ./models
RUN \
    /installer.sh /packages/shared_db &&\
    /installer.sh /packages/shared_models &&\
    /installer.sh /packages/shared_schemas &&\
    /installer.sh /packages/shared_utils &&\
    /installer.sh /packages/models

# -----------------------------
# 4. Copy app
# -----------------------------
ARG APPLICATION=1
WORKDIR /api

COPY Core/src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY Core/src/main.py ./main.py
COPY Core/src/application ./application
COPY Core/src/domain ./domain
COPY Core/src/infrastructure ./infrastructure
COPY Core/src/routers ./routers
COPY Core/src/schemas ./schemas
COPY Core/src/utils ./utils

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Core/entrypoint_core.sh /entrypoint_core.sh
RUN chmod +x /entrypoint_core.sh
ENTRYPOINT ["/entrypoint_core.sh"]

# -----------------------------
# 6. Run uvicorn
# -----------------------------
CMD ["sh", "-c", "uvicorn main:api --host 0.0.0.0 --port ${PORT_CORE:-8000}"]
