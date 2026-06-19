FROM docker.io/labcapital/apps:app-Base

ARG APPLICATION=1
WORKDIR /api

COPY Auth/src/pyproject.toml ./pyproject.toml

# Mock layout to satisfy Hatchling and cache heavy libraries (FastAPI, Argon2, etc.)
RUN mkdir -p application domain infrastructure routers schemas utils \
  && touch main.py \
  && pip install --no-cache-dir .

# ----------------------------------------------------------------------
# CACHE BOUNDARY
# ----------------------------------------------------------------------
COPY Auth/src/main.py ./main.py
COPY Auth/src/application ./application
COPY Auth/src/domain ./domain
COPY Auth/src/infrastructure ./infrastructure
COPY Auth/src/routers ./routers
COPY Auth/src/schemas ./schemas
COPY Auth/src/utils ./utils

RUN pip install --no-cache-dir --no-deps .

COPY Auth/entrypoint_auth.sh /entrypoint_auth.sh
RUN chmod +x /entrypoint_auth.sh
ENTRYPOINT ["/entrypoint_auth.sh"]

CMD ["sh", "-c", "exec uvicorn main:api --host 0.0.0.0 --port $PORT_AUTH"]
