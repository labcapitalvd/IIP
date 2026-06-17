# =================================================
# Stage 1: Start application
# =================================================
FROM docker.io/labcapital/apps:app-Base

# -----------------------------
# 4. Copy app
# -----------------------------
ARG APPLICATION=1
WORKDIR /api

COPY Core/src/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY Core/src/main.py ./main.py
COPY Core/src/application ./application
COPY Core/src/domain ./domain
COPY Core/src/infrastructure ./infrastructure
COPY Core/src/routers ./routers
COPY Core/src/schemas ./schemas
COPY Core/src/utils ./utils

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
