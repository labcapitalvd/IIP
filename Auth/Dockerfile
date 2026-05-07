# =================================================
# Stage 1: Start application
# =================================================
FROM labcapital/apps:IIP-Base 

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
