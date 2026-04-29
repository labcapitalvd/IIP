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
RUN pip install --no-cache-dir /packages/shared_db
RUN pip install --no-cache-dir /packages/shared_models
RUN pip install --no-cache-dir /packages/shared_schemas
RUN pip install --no-cache-dir /packages/shared_utils

# -----------------------------
# 4. Copy app
# -----------------------------
ARG APPLICATION=1
WORKDIR /api

COPY Auth/src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY Auth/src/main.py ./main.py
COPY Auth/src/application ./application
COPY Auth/src/domain ./domain
COPY Auth/src/infrastructure ./infrastructure
COPY Auth/src/routers ./routers
COPY Auth/src/schemas ./schemas
COPY Auth/src/utils ./utils

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Auth/entrypoint_auth.sh /entrypoint_auth.sh
RUN chmod +x /entrypoint_auth.sh
ENTRYPOINT ["/entrypoint_auth.sh"]

# -----------------------------
# 6. Run uvicorn
# -----------------------------
CMD ["sh", "-c", "uvicorn main:api --host 0.0.0.0 --port ${PORT_AUTH:-8000}"]
