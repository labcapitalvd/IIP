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
RUN --mount=type=secret,id=github_token_commons \
    export GITHUB_TOKEN_COMMONS=$(cat /run/secrets/github_token_commons) && \
    curl -L -H "Authorization: token ${GITHUB_TOKEN_COMMONS}" \
    -H "Accept: application/vnd.github.v3.raw" \
    "https://api.github.com/repos/LABCapital-VD/Commons/contents/Packages/shared_utils/fetch.sh?ref=main" \
    -o /usr/local/bin/fetch.sh && \
    chmod +x /usr/local/bin/fetch.sh

ARG CACHEBUST=1
# Fetch/install each package
RUN --mount=type=secret,id=github_token_commons \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_db.zip
RUN --mount=type=secret,id=github_token_commons \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_models.zip
RUN --mount=type=secret,id=github_token_commons \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_schemas.zip
RUN --mount=type=secret,id=github_token_commons \
    /usr/local/bin/fetch.sh LABCapital-VD/Commons shared_utils.zip
RUN --mount=type=secret,id=github_token_iip \
    /usr/local/bin/fetch.sh LABCapital-IIP/IIP-Persistence models.zip

# -----------------------------
# 3. Config virtual environment
# -----------------------------
COPY src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

# -----------------------------
# 4. Copy app
# -----------------------------
COPY src/migrator ./migrator
COPY src/schemer ./schemer
COPY src/seeder ./seeder

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY entrypoint_pers.sh /entrypoint_pers.sh
RUN chmod +x /entrypoint_pers.sh
ENTRYPOINT ["/entrypoint_pers.sh"]
