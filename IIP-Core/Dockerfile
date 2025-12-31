# =================================================
# Stage 1: Start application
# =================================================
FROM python:3.14-slim-bookworm
WORKDIR /api
RUN apt-get update && apt-get install -y \
    gcc\
    g++\
    libpq-dev\
    curl\
    jq\
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 2. Install shared packages from GitHub
# -----------------------------
RUN --mount=type=secret,id=github_token \
    GITHUB_TOKEN=$(cat /run/secrets/github_token) && \
    curl -L -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    https://raw.githubusercontent.com/LABCapital-VD/Commons/main/Packages/shared_utils/fetch.sh \
    -o /usr/local/bin/fetch.sh && \
    chmod +x /usr/local/bin/fetch.sh

# -----------------------------
# 3. Config virtual environment
# -----------------------------
ARG CACHEBUST=1
# Fetch/install each package
RUN --mount=type=secret,id=github_token \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_db.zip
RUN --mount=type=secret,id=github_token \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_models.zip
RUN --mount=type=secret,id=github_token \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_schemas.zip
RUN --mount=type=secret,id=github_token \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_utils.zip
RUN --mount=type=secret,id=github_token \
    /usr/local/bin/fetch.sh LABCapital-IIP/IIP-Persistence models.zip

COPY src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

# -----------------------------
# 4. Copy app
# -----------------------------
COPY src/main.py ./main.py
COPY src/db ./db
COPY src/handlers ./handlers
COPY src/routers ./routers
COPY src/schemas ./schemas

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
