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
COPY src/main.py ./main.py
COPY src/application ./application
COPY src/domain ./domain
COPY src/infrastructure ./infrastructure
COPY src/routers ./routers
COPY src/schemas ./schemas
COPY src/utils ./utils

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY entrypoint_core.sh /entrypoint_core.sh
RUN chmod +x /entrypoint_core.sh
ENTRYPOINT ["/entrypoint_core.sh"]

# -----------------------------
# 6. Run uvicorn
# -----------------------------
CMD ["sh", "-c", "uvicorn main:api --host 0.0.0.0 --port ${PORT_CORE:-8000}"]
