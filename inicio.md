# IIP — Índice de Innovación Pública · Guía de inicio

> Generado el 2026-10-07 tras revisar el repo y el estado de Docker en WSL2. Rama actual: `login-ch`.

## 1. Estado actual (2026-10-07)

| Servicio | Contenedor | Puerto host | Estado |
|---|---|---|---|
| Frontend (React + nginx) | `app_frontend` | **4287** (http) | Corriendo, responde `200`. Docker lo marca `unhealthy` (ver §6) |
| Valkey (caché/sesiones) | `app_cache` | **6379** | Corriendo, `healthy` |
| nginx gateway (HTTPS) | `app_nginx` | 4288 (Auth), 4289 (Core) previstos | **Reiniciándose en bucle** — no escucha |
| Auth API | `app_auth` | interno 4288 | **Detenido** (`Exited (0)`, hace 2 semanas) |
| Core API | `app_core` | interno 4289 | **Detenido** |
| PostgreSQL 18 | `app_db` | 5432 | **Detenido** |
| Persister (migraciones/seed) | `app_persister` | — | Detenido (job batch, es normal) |
| Base (imagen) | `app_base` | — | Detenido (solo existe para construir la imagen) |

**Conclusión: el proyecto está parcialmente levantado.** Solo frontend y caché funcionan. El backend (Auth, Core, DB) no corre, así que el login/registro real falla. `app_nginx` se cae con `host not found in upstream "auth"` porque el contenedor `auth` no existe en ejecución.

Puertos en escucha en el host: `4287` y `6379` (confirmado con `ss -ltn`). `4288`, `4289` y `5432` no responden.

## 2. Qué es el proyecto

Monorepo Python (DDD / arquitectura limpia) + frontend React, orquestado con Docker Compose. Plataforma para diseñar formularios dinámicos, recibir envíos (submissions) y evaluarlos, con autenticación JWT y control de acceso RBAC/ReBAC. Repo: `labcapitalvd/IIP`.

```
.
├── Auth/                      # Microservicio de autenticación (FastAPI)
├── Core/                      # Microservicio de negocio: actores, formularios, envíos, resultados
├── Persistence/               # Alembic, seeder, populator (job `persister`)
├── Packages/                  # shared, shared_schemas, shared_utils (código común)
├── Scripts/                   # launcher.sh (operaciones), secrets.sh (genera secretos)
├── Secrets/ · Secrets_Template/  # Secretos locales (gitignored) y plantillas
├── Documentación/             # ARQUITECTURA_BACKEND.md, informe en Typst
├── indice-de-innovacion-publica/  # Frontend React 19 + Vite + TS + Tailwind
├── compose.yaml               # Orquestación local
├── Dockerfile                 # Imagen base compartida (app-base)
├── cambios.md                 # Bitácora detallada de cambios y pendientes
└── Readme.md
```

## 3. Arquitectura y puertos

```
Navegador ──http──▶ Frontend :4287 (nginx estático)
    │
    └─https (cert autofirmado)─▶ app_nginx ─┬─ :4288 ─▶ auth:4288 (FastAPI)
                                            └─ :4289 ─▶ core:4289 (FastAPI)
                                   auth/core ─▶ Postgres (db:5432) · Valkey (cache:6379)
```

- Rango de puertos del proyecto: **4287–4290** (4290 libre). Definidos en `.env` (`PORT_AUTH=4288`, `PORT_CORE=4289`) y en `Secrets/nginx.conf`.
- Los puertos 5432 (Postgres) y 6379 (Valkey) están publicados al host; `compose.yaml` indica eliminarlos luego para no exponerlos.
- Redes Docker: `app_db_network`, `app_nginx_network`, `app_cache_network`. Volumen de datos Postgres: `pg`.
- CORS: `PUBLIC_ORIGINS=*`, `PRIVATE_ORIGINS=*`, `PRODUCTION_MODE=false` (modo desarrollo).

### Stack
Python 3.12 · FastAPI/uvicorn · SQLAlchemy + Alembic · PostgreSQL 18 · Valkey · JWT ED25519 · Fernet · uv (workspace) · Nix flakes (opcional) · React 19 + Vite 6 + Tailwind.

## 4. Cómo levantar todo

Desde la raíz del repo, en WSL:

```bash
# 1. Secretos (solo la primera vez; ya existen en ./Secrets)
cd Scripts && ./secrets.sh && cd ..

# 2. Construir en orden (auth/core/persister parten de la imagen app-base local)
docker compose build base
docker compose build auth core persister frontend

# 3. Base de datos + migraciones + seed (primera vez o tras limpiar el volumen `pg`)
cd Scripts && ./launcher.sh --setup && cd ..

# 4. Levantar el resto
docker compose up -d
```

Verificación:

```bash
docker ps
curl -I http://localhost:4287          # frontend
curl -k https://localhost:4288/docs    # Auth (cert autofirmado → -k)
curl -k https://localhost:4289/docs    # Core
```

Otras operaciones (`Scripts/launcher.sh`): `--revision "nombre"`, `--extract`, `--backup`, `--restore <archivo.sql>`.

Desarrollo del frontend sin Docker: `cd indice-de-innovacion-publica && npm install && npm run dev` (puerto 3000).

## 5. Módulos y endpoints principales

- **Auth**: `routers/auth.py`, `routers/files.py`. Login, registro (asigna rol `standard_user`, enlaza actor, crea `UserDetails`), refresh y `GET /public/auth/me`.
- **Core**: `routers/actors.py`, `forms.py`, `submissions.py`, `results.py`. Existe `POST /forms` y `POST /submissions/forms/{form_id}`; no hay `PUT`/`DELETE` de formularios ni `GET /submissions`.
- **Frontend**: `apiClient.ts` decide entre backend real (`useRealBackend`) y modo mock (`localStorage`). Vistas reales: login/registro, actores, segmentos. Mock: usuarios de entidad, asignaciones.
- Detalle completo (diagramas ER, flujo JWT, endpoints): `Documentación/ARQUITECTURA_BACKEND.md`.

## 6. Problemas detectados y siguientes pasos

1. **Backend caído.** Reconstruir y levantar (§4). Los dos bloqueos históricos, según `cambios.md` (2026-09-17), ya tienen fix en el árbol de trabajo pero **sin confirmar con Docker**:
   - `entrypoint.sh` con CRLF (`exec /entrypoint.sh: no such file or directory`). Falta `git add --renormalize .` para fijarlo.
   - Layout `services/` → `application/` + `domain/` plano (`ImportError: cannot import name 'AuthAppService'`).
2. **`app_nginx` en bucle** — se resuelve solo cuando `auth` y `core` estén en ejecución.
3. **Frontend `unhealthy`** pese a responder 200 desde el host. Hipótesis (no verificada): el healthcheck usa `wget http://localhost:4287/` y `localhost` resuelve a IPv6 (`::1`) donde nginx no escucha; probar con `127.0.0.1`.
4. **Imágenes con 2 semanas**: la imagen del frontend en ejecución podría no incluir los últimos cambios; reconstruir.
5. **Árbol de trabajo muy modificado** en `login-ch` (renombres masivos sin commit). Conviene commitear tras verificar que todo arranca.
6. **Seguridad**: `.env` tiene contraseñas débiles reutilizadas (Postgres y tokens de GitHub); `Core` no aplica autorización granular; token inválido en `Core` responde 500 en lugar de 401; `POST /submissions` tiene bugs conocidos (ver `cambios.md`, sección «Pendientes»).
7. Código muerto en `Core/src/application/alejo.py`, `form_design.py` y `domain/services/alejo.py`.

## 7. Referencias
- `Readme.md` — guía general · `cambios.md` — historial y pendientes · `Documentación/ARQUITECTURA_BACKEND.md` — arquitectura.
- Secretos: no se versionan (`Secrets/`, `.env`); plantillas en `Secrets_Template/`.
