# =================================================
# Stage 2: Final Application Layer
# =================================================
FROM docker.io/labcapital/apps:app-base

ARG APPLICATION=1
WORKDIR /api

# 1. Copy ONLY the configuration first
COPY Core/src/pyproject.toml ./pyproject.toml

# Mock layout to satisfy Hatchling and cache heavy libraries (FastAPI, Argon2, etc.)
RUN mkdir -p application domain infrastructure routers schemas utils \
  && touch main.py \
  && pip install --no-cache-dir .

# -----------------------------
# CACHE BOUNDARY
# -----------------------------
# 3. Overwrite the mock folders with your actual real implementation code
COPY Core/src/main.py ./main.py
COPY Core/src/infrastructure/ ./infrastructure/
COPY Core/src/routers/ ./routers/
COPY Core/src/schemas/ ./schemas/
COPY Core/src/services/ ./services/
COPY Core/src/utils/ ./utils/

# -----------------------------
# 4. Re-run a fast, local-only install to sync your actual code metadata 
# -----------------------------
RUN pip install --no-cache-dir --no-deps .

# -----------------------------
# 5. configure ports
# -----------------------------
ARG PORT_CORE=8001
ENV PORT_CORE=${PORT_CORE}
EXPOSE ${PORT_CORE}

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Core/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# -----------------------------
# 6. Run uvicorn
# -----------------------------
CMD ["sh", "-c", "exec uvicorn main:api --host 0.0.0.0 --port $PORT_CORE"]
