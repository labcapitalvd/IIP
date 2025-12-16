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
COPY fetch.sh /usr/local/bin/fetch.sh
RUN chmod +x /usr/local/bin/fetch.sh

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

# -----------------------------
# 3. Config virtual environment
# -----------------------------
COPY src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir -e .

# -----------------------------
# 4. Copy app
# -----------------------------
COPY src/main.py ./main.py

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY entrypoint_agent.sh /entrypoint_agent.sh
RUN chmod +x /entrypoint_agent.sh
ENTRYPOINT ["/entrypoint_agent.sh"]

# -----------------------------
# 6. Run uvicorn
# -----------------------------
CMD ["sh", "-c", "uvicorn main:api --host 0.0.0.0 --port ${PORT_IA_AGENT:-8000}"]
