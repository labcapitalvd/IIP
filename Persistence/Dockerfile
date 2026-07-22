# =================================================
# Stage 2: Final Application Layer
# =================================================
FROM docker.io/labcapital/apps:app-base

ARG APPLICATION=1
WORKDIR /api

# 1. Copy ONLY the configuration first
COPY Persistence/src/pyproject.toml ./pyproject.toml

# Mock layout to satisfy Hatchling and cache heavy libraries (FastAPI, Argon2, etc.)
RUN mkdir -p migrator schemer seeder populator scripts \
  && pip install --no-cache-dir .

# -----------------------------
# CACHE BOUNDARY
# -----------------------------
# 3. Overwrite the mock folders with your actual real implementation code
COPY Persistence/src/migrator ./migrator
COPY Persistence/src/schemer ./schemer
COPY Persistence/src/seeder ./seeder
COPY Persistence/src/populator ./populator
COPY Persistence/src/scripts ./scripts

# -----------------------------
# 4. Re-run a fast, local-only install to sync your actual code metadata 
# -----------------------------
RUN pip install --no-cache-dir --no-deps .

# -----------------------------
# 5. configure ports
# -----------------------------
ARG PORT_AUTH=8000
ARG PORT_CORE=8001
ENV PORT_AUTH=${PORT_AUTH}
ENV PORT_CORE=${PORT_CORE}

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Persistence/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
