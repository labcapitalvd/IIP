# =================================================
# Stage 1: Start application
# =================================================
FROM labcapital/apps:IIP-Base

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
COPY Persistence/src/populator ./populator
COPY Persistence/src/scripts ./scripts

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Persistence/entrypoint_pers.sh /entrypoint_pers.sh
RUN chmod +x /entrypoint_pers.sh
ENTRYPOINT ["/entrypoint_pers.sh"]
