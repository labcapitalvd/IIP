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
ARG FETCHER=1
RUN --mount=type=secret,id=github_token_commons \
    export GITHUB_TOKEN_COMMONS=$(cat /run/secrets/github_token_commons) && \
    curl -L -H "Authorization: token ${GITHUB_TOKEN_COMMONS}" \
    -H "Accept: application/vnd.github.v3.raw" \
    "https://api.github.com/repos/LABCapital-VD/Commons/contents/Packages/shared_utils/fetch.sh?ref=main" \
    -o /usr/local/bin/fetch.sh && \
    chmod +x /usr/local/bin/fetch.sh

# -----------------------------
# 3. Config virtual environment
# -----------------------------
ARG PACKAGES=1
# Fetch/install each package
RUN --mount=type=secret,id=github_token_commons \
    TOKEN=$(cat /run/secrets/github_token_commons) && \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_db.zip "$TOKEN" && \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_models.zip "$TOKEN" && \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_schemas.zip "$TOKEN" && \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_utils.zip "$TOKEN"

RUN --mount=type=secret,id=github_token_iip \
    TOKEN=$(cat /run/secrets/github_token_iip) && \
    /usr/local/bin/fetch.sh LABCapital-IIP/IIP-Persistence models.zip "$TOKEN"

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
