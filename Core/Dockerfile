# =================================================
# Stage 2: Final Application Layer
# =================================================
FROM docker.io/labcapital/apps:app-Base

ARG APPLICATION=1
WORKDIR /api

# 1. Copy ONLY the configuration first
COPY Core/src/pyproject.toml ./pyproject.toml

# 2. Trick Hatchling into caching your external dependencies (FastAPI, Pandas, etc.)
# by creating mock folders so its validation pass succeeds.
RUN mkdir -p application domain infrastructure routers schemas utils \
  && touch main.py \
  && pip install --no-cache-dir .

# ----------------------------------------------------------------------
# CACHE BOUNDARY! Changing your Python code will only execute from here down.
# ----------------------------------------------------------------------

# 3. Overwrite the mock folders with your actual real implementation code
COPY Core/src/main.py ./main.py
COPY Core/src/application/ ./application/
COPY Core/src/domain/ ./domain/
COPY Core/src/infrastructure/ ./infrastructure/
COPY Core/src/routers/ ./routers/
COPY Core/src/schemas/ ./schemas/
COPY Core/src/utils/ ./utils/

# 4. Re-run a fast, local-only install to sync your actual code metadata 
RUN pip install --no-cache-dir --no-deps .

# -----------------------------
# 5. setup entrypoint
# -----------------------------
COPY Core/entrypoint_core.sh /entrypoint_core.sh
RUN chmod +x /entrypoint_core.sh
ENTRYPOINT ["/entrypoint_core.sh"]

# -----------------------------
# 6. Run uvicorn
# -----------------------------
CMD ["sh", "-c", "exec uvicorn main:api --host 0.0.0.0 --port $PORT_CORE"]
