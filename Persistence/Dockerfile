FROM docker.io/labcapital/apps:app-base

ARG APPLICATION=1
WORKDIR /api

COPY Persistence/src/pyproject.toml ./pyproject.toml

# Mock the structure for the initial heavy pip download pass
RUN mkdir -p migrator schemer seeder populator scripts \
  && pip install --no-cache-dir .

# ----------------------------------------------------------------------
# CACHE BOUNDARY
# ----------------------------------------------------------------------
COPY Persistence/src/migrator ./migrator
COPY Persistence/src/schemer ./schemer
COPY Persistence/src/seeder ./seeder
COPY Persistence/src/populator ./populator
COPY Persistence/src/scripts ./scripts

RUN pip install --no-cache-dir --no-deps .

COPY Persistence/entrypoint_pers.sh /entrypoint_pers.sh
RUN chmod +x /entrypoint_pers.sh
ENTRYPOINT ["/entrypoint_pers.sh"]
