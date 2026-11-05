# Historial de cambios — IIP

> Registro de trabajo realizado en la rama `cambios-alejo`. Pensado para que quien retome el proyecto (incluido tú mismo más adelante) entienda qué se tocó, por qué, y qué quedó pendiente — sin tener que releer todo el historial de commits o de conversación.

---

## 2026-09-15 — Sesión: despliegue, arquitectura, endpoint de formularios, frontend y autenticación real

### 1. Secretos y despliegue (`docker compose up`)

El repo tenía el flujo de secretos (`Scripts/secrets.sh`, `secrets.yaml` + SOPS/age) parcialmente aplicado: faltaban archivos que `compose.yaml` exige como Docker secrets, así que `docker compose up` fallaba antes de arrancar nada.

- Generados en `./Secrets/`: `postgres_password`, `valkey_password` (nuevo, aleatorio — no existía ninguna `VALKEY_PASSWORD`), `fernet_password`, `github_token_{commons,iip,seeds}`, `nginx.conf`.
- Agregada `VALKEY_PASSWORD` a `.env` (el servicio `cache` la necesita para `--requirepass`).
- **Bug corregido en `Secrets/nginx.conf`**: la plantilla traía los puertos hardcodeados en 8000/8001, pero `.env` usa `PORT_AUTH=4293` / `PORT_CORE=4294`. Con la plantilla original, nginx habría enrutado a puertos donde no había nada escuchando. Se generó el archivo con los puertos correctos.
- Eliminada una carpeta vacía `./nginx.conf` (residuo de un mount fallido previo).
- **Pendiente que sigue igual**: `POSTGRES_PASSWORD` y los tres `GITHUB_TOKEN_*` en `.env`/`Secrets_Template/.env` reutilizan la misma contraseña débil. No se tocó porque es decisión del dueño del `.env` local (está en `.gitignore`, no llegó a git).
- **Bug de build encontrado al primer `docker compose up --build`**: `Auth`, `Core` y `Persistence` parten de `docker.io/labcapital/apps:app-base`, que es la imagen que construye el servicio `base` del `Dockerfile` raíz — no una imagen pública. Si se construye todo junto sin orden, Docker intenta bajarla de Docker Hub y falla. Solución: `docker compose build base` antes que el resto (o `docker compose build base auth core persister` en ese orden).

### 2. Documentación de arquitectura

Creado **[`Documentación/ARQUITECTURA_BACKEND.md`](Documentación/ARQUITECTURA_BACKEND.md)**: diagrama de arquitectura general (Nginx → Auth/Core → Postgres/Valkey + job batch `persister`), flujo de autenticación JWT con diagrama de secuencia, modelo RBAC+ReBAC, tabla completa de endpoints (montados vs. no), pipeline de inicialización (`schemer → alembic → seeder → populator` vía `launcher.sh`), y **7 diagramas ER en Mermaid** cubriendo las ~45 tablas del esquema multi-schema de Postgres.

Se mantiene actualizado a medida que se corrigen cosas (ver §3 más abajo, ya reflejado ahí).

### 3. Endpoint `POST /forms` (Core) — de roto/duplicado a funcional

Había **tres implementaciones en conflicto** del mismo endpoint, ninguna funcional:
- `routers/alejo.py` + `application/alejo.py` + `domain/services/alejo.py`: import roto (`application.forms` no existía), usaba campos inventados (`anno`, `title`) que no existen en los modelos reales (`code`, `label`), y construía FKs manualmente antes de tener el `id` (los UUID se generan server-side, siempre habrían sido `NULL`).
- `routers/forms.py` + `application/form_design.py`: código muerto, copiado de `actors.py` por error (usaba `ActorSchema`/`uow.actors` dentro de un `FormDesignUoW` que no tiene ese repo).
- `domain/services/forms.py`: contenía métodos de `Actor` copiados, no lógica de formularios.

**Solución**: se consolidó todo en `routers/forms.py` → `application/forms.py` → `domain/services/forms.py` (se eliminaron los archivos `alejo.py` y el duplicado muerto). El schema de request ahora usa `code`/`label`/`description` igual que las columnas reales, y anida `field_groups` dentro de `card_template` (antes colgaban directo de `question`, que no es como está la FK real: toda `Question` tiene siempre un `CardTemplate` 1:1 obligatorio). La construcción del árbol completo (`Form → Section* → Question → CardTemplate → FieldGroup → Field → FieldChoice`) se hace vía relaciones de SQLAlchemy (`cascade="save-update"`), no asignando IDs a mano. Ya está montado en `Core/src/main.py`.

Ejemplo de payload y curl de prueba: ver conversación / `Documentación/ARQUITECTURA_BACKEND.md` §8.3.

### 4. Frontend integrado a Docker

Se encontró el proyecto frontend preliminar en `indice-de-innovacion-publica/` (React 19 + Vite + TS + Tailwind, generado con AI Studio).

- Creado `indice-de-innovacion-publica/Dockerfile` (build multi-etapa: `node:22-alpine` → `nginx:stable-alpine` sirviendo el `dist/` estático con el `nginx.conf` que ya traía el proyecto).
- Agregado el servicio `frontend` a `compose.yaml` (puerto `3000`, red `app_nginx`, `depends_on: auth, core`).
- **Bug corregido**: `apiClient.ts` traía `authBaseUrl`/`coreBaseUrl` en `http://`, pero el `nginx` del backend solo escucha `ssl` en 4293/4294 (certificado autofirmado, sin listener en texto plano). Cambiado a `https://`.
- Verificado con `npm install && npm run build` localmente (no hay lockfile en el repo, así que es `npm install`, no `npm ci`) — compila limpio.
- El `docker-compose.yml` propio del frontend se dejó intacto por si se quiere levantar aislado, pero ya no es necesario: `compose.yaml` en la raíz levanta todo junto.

### 5. Login y registro del frontend conectados al backend real (JWT)

El frontend ya tenía `apiClient`/`authService` bien escritos para hablar con la API real, pero `AuthContext` nunca los dejaba actuar: antes de intentar login/registro reales, siempre revisaba primero una base de usuarios falsa en `localStorage` (`DEMO_USERS` + auto-registrados), con contraseñas "maestras" (`admin1234`, `12345678`, `Bogota2026*`) de por medio, y el registro guardaba todo en `localStorage` con un estado "pendiente de aprobación" que **no existe en el backend real** (ahí el registro activa la cuenta de inmediato).

- `AuthContext.login()`/`register()` ahora bifurcan explícitamente en `apiClient.getConfig().useRealBackend`: en modo real van directo a la API sin atajos locales; en modo mock se conserva el comportamiento simulado de siempre (para seguir probando la UI sin backend levantado).
- El arranque de la app ya no fuerza una sesión falsa de admin cuando `useRealBackend` está activo.
- Nuevo `src/utils/jwt.ts`: decodifica el payload del JWT en el navegador (sin verificar firma — eso es del backend) para leer `sub`/`username`/`exp`.
- Restauración de sesión al recargar: si el `access_token` guardado expiró, intenta `reauth()` silencioso con el `refresh_token`; si también falla, cierra sesión en vez de quedar "logueado" con un token muerto.
- Validaciones del formulario de registro alineadas a las reglas reales del backend (usuario 4-128 caracteres, contraseña 8-128 — antes pedía mínimo 6, lo que habría producido un `422` sorpresa).
- Textos de UI ("pendiente de aprobación", accesos rápidos demo) ahora condicionados a `useRealBackend`, para no mentirle al usuario sobre el estado real de su cuenta.

### 6. Backend: datos de usuario faltantes + `GET /auth/me`

**Bug crítico encontrado**: `TierRepository.get_default()` filtraba `UserTier.label == "STANDARD"`, pero los tiers sembrados tienen `code="standard"` / `label="Standard Tier"`. **El registro fallaba con 500 en cualquier base de datos recién sembrada, sin excepción** — bloqueaba todo registro real. Corregido para filtrar por `code` con el valor correcto.

El frontend (`authService.ts`) ya enviaba `actor_id`, `contact_person`, `phone` al registrar, pero el backend los ignoraba (Pydantic descarta campos no declarados) y solo creaba la fila `User`, sin tocar `UserDetails` / `UserActorLink` / `UserSystemRoleLink` — tablas que **ya existían en el modelo y en la migración inicial**, simplemente no se usaban. No hizo falta ninguna migración nueva.

- `Auth/src/schemas/auth.py`: `RequestRegister` declara explícitamente `actor_id`, `contact_person`, `phone`.
- `Auth/src/domain/services/auth/auth.py`: `register()` ahora valida email único (antes solo username), asigna el rol global `standard_user` a todo usuario nuevo, enlaza al `Actor` si se envió `actor_id` (con 404 si no existe), y crea `UserDetails` si se envió `contact_person`.
- Nuevo **`GET /public/auth/me`**: antes el frontend no tenía forma de saber el rol/entidad de un usuario real (el JWT solo trae `sub`/`username`). Ahora decodifica el token, consulta la BD (`UserRepository.get_with_auth_context`, ampliado para traer también `tier`, `actor_links.actor` y `details`) y devuelve `id`, `username`, `email`, `is_active`, `tier`, `system_roles[]`, `actor_links[]`, `name`, `phone`.
- `authService.ts`/`AuthContext.tsx`: el perfil del usuario ya **no se cachea en `localStorage`/`sessionStorage`** en modo real — se pide fresco a `/auth/me` después del login y en cada montaje de la app (refrescando el token primero si expiró). El backend es la única fuente de verdad, tal como se pidió.

Verificación hecha en esta sesión (sin Docker disponible en el entorno de trabajo, así que no se probó end-to-end en contenedores):
- `python3 -m py_compile` sobre todos los archivos Python tocados — sin errores.
- `tsc --noEmit` y `npm run build` en el frontend — 0 errores, build limpio, antes y después de cada tanda de cambios.
- Confirmado contra la migración `4af16f57b7da_initial.py` que las tablas usadas (`user_details`, `user_actor_links`, `user_system_role_links`, `system_roles`) ya existen en Postgres.

### 7. Frontend — auditoría real-vs-mock y corrección de "engaños" en el gestor de formularios y el monitor de radicados

Sesión enfocada exclusivamente en `indice-de-innovacion-publica/` (la vista), sin tocar backend. Antes de escribir código se auditó, componente por componente, qué vistas ya hablan con la API real y cuáles siguen siendo simulación local (`AppContext` + `localStorage`):

- **Ya reales y completos**: Login/Registro (`LoginView` + `AuthContext`, incluye `GET /auth/me`), CRUD de Actores y de Segmentos (`ActorsManager`/`SegmentsManager`, Create/Read/Delete reales — no hay Update porque el backend no expone `PUT`).
- **Mock 100% (sin endpoint en el backend para soportarlo)**: `EntityUsersManager` (administración de usuarios), `FormAssignmentsManager` (asignaciones) — comportamiento esperado, no se tocaron.
- **Bug encontrado — "editar formulario" duplica en el servidor real**: como `Core` solo tiene `POST /forms` (sin `PUT`), `FormsManager`/`FormBuilderModal` reenviaban el formulario completo por el mismo `POST` tanto al crear como al editar. Cada "guardar" de un formulario ya sincronizado creaba un registro **nuevo y huérfano** en el backend, invisible desde la UI (que seguía mostrando el mismo formulario local), sin ningún aviso al usuario.
  - **Fix**: nuevo campo `IIPForm.is_synced_to_backend` (`types/index.ts`), fijado en `true` por `AppContext.saveFormDefinition` tras el primer `POST /forms` exitoso y propagado a través de `FormBuilderModal.handleSave`. `FormsManager` ahora pide confirmación explícita (`confirmDuplicateSyncIfNeeded`) antes de reenviar un formulario ya sincronizado, explicando que se creará un duplicado en vez de actualizar; lo mismo al eliminar un formulario ya sincronizado (el backend tampoco tiene `DELETE /forms`, así que "eliminar" solo lo quita de la lista local). Se agregaron badges visuales ("● Sincronizado con backend" / "○ Solo local") en las tarjetas de formularios y en el encabezado del formulario seleccionado, visibles solo en modo backend real.
- **Bug encontrado — label engañoso en `SubmissionsMonitor`**: la cabecera mostraba el tag `/public/submissions` dando a entender que la tabla se carga con un `GET` real, pero ese endpoint no existe en el backend (`Core` solo tiene `POST /submissions/forms/{form_id}`); la tabla siempre fue datos locales (`localStorage` + lo que se agrega tras un envío real en la sesión). Se reemplazó el tag por un aviso explícito en ámbar ("Vista local — sin GET /submissions en el backend") con tooltip, y se aclaró el texto descriptivo de la vista.
- **Limpieza de código muerto**: `AuthModal.tsx` (componente huérfano, no importado en ningún lado — la app usa `LoginView`) se eliminó; se quitaron de `Header.tsx` las props `onOpenAuthModal`/`onOpenDockerModal`, declaradas pero nunca usadas.

Verificación: `npm install` (dependencias no estaban instaladas en este entorno) + `npm run lint` (`tsc --noEmit`) sin errores tras todos los cambios. No se pudo hacer verificación visual en navegador headless (Playwright no logró descargar el binario de Chromium por falta de acceso de red saliente en este entorno) — pendiente probar manualmente en un navegador real antes de dar por cerrado.

**Nota de alcance**: se detectaron otros componentes huérfanos no importados en ninguna parte (`DockerDeploymentModal.tsx`, `HttpLogsDrawer.tsx`, `ApiTesterConsole.tsx`) que no se tocaron por no estar dentro del alcance acordado en esta sesión — candidatos a limpieza futura si se confirma que no están pensados para integrarse pronto.

---

## 2026-09-17 — Sesión (rama `login-ch`): despliegue roto — puertos, `entrypoint.sh` con CRLF y el layout `services/` vs. `application`/`domain` plano

Nota: a mitad de la sesión anterior el checkout local pasó de `cambios-alejo` a `login-ch` (aparentemente por fuera de esta conversación — se detectó un `git log` distinto y un stash `WIP on main` pendiente). Todo lo de esta sección se hizo sobre `login-ch`, que **diverge de `cambios-alejo`**: no tiene el cleanup de `alejo.py` en `Core` ni, como se descubre abajo, el mismo layout de carpetas para `application`/`domain`.

### 1. Cambio de rango de puertos a 4287–4290

A pedido del usuario (puertos 4293/4294 chocaban con otra cosa en su máquina): **frontend `4287` · Auth `4288` · Core `4289`** (`4290` libre). Actualizado en `.env`, `Secrets_Template/.env`, `Secrets/nginx.conf` (listen + `proxy_pass`), `compose.yaml` (puerto publicado de `frontend`), `indice-de-innovacion-publica/Dockerfile` + su `nginx.conf` interno + su `docker-compose.yml` standalone, `src/services/apiClient.ts` (URLs por defecto que usa el navegador) y el pill de estado en `src/App.tsx`. También se sincronizó `Documentación/ARQUITECTURA_BACKEND.md`.

### 2. `docker ps` no mostraba `auth`/`core` y `nginx` estaba en `Restarting (1)`

Diagnóstico en dos capas, confirmado con los logs reales que pegó el usuario (`docker logs app_auth` / `app_core` / `app_nginx`):

- **Causa inmediata de que `nginx` reiniciara en bucle**: `host not found in upstream "auth"` — nginx no podía resolver el contenedor `auth` porque ese contenedor no llegaba a arrancar.
- **Por qué `auth` no arrancaba (capa 1)**: `exec /entrypoint.sh: no such file or directory`. Los scripts `Auth/entrypoint.sh`, `Core/entrypoint.sh`, `Persistence/entrypoint.sh`, `Scripts/launcher.sh` y `Scripts/secrets.sh` tenían terminadores **CRLF** (Windows) en vez de LF — con CRLF el shebang `#!/bin/sh` se lee como `#!/bin/sh\r`, un intérprete que no existe. **Fix**: los 5 se normalizaron a LF. Ya existía un `.gitattributes` con `*.sh text eol=lf` (agregado por el usuario, sin trackear todavía) que debería evitar que esto se repita — pero como los blobs ya estaban commiteados en CRLF de antes, la regla nunca se había aplicado retroactivamente; falta `git add --renormalize .` para que el fix quede permanente en el repo.
- **Por qué seguía fallando tras el fix de CRLF (capa 2, la gorda)**: una vez que `auth`/`core` arrancaban, uvicorn tiraba `ImportError: cannot import name 'AuthAppService' from 'application' (unknown location)` (y lo mismo con `IdentityAppService` en `core`). Causa raíz: **`login-ch` tiene el código real de la capa de aplicación/dominio bajo `Auth/src/services/{application,domain}/` y `Core/src/services/{application,domain}/`**, pero `Auth/src/pyproject.toml` / `Core/src/pyproject.toml` (Hatchling `packages = [...]`) y ambos `Dockerfile` siguen esperando el layout **plano** `src/application/` + `src/domain/` (así lo importan los routers: `from application import AuthAppService`, etc.). El `Dockerfile` sólo copiaba `services/` al build — nunca copiaba nada a `./application/`/`./domain/`, así que esas carpetas quedaban vacías dentro de la imagen (solo el mock `mkdir -p` de la etapa de cache de Hatchling), de ahí el `(unknown location)`.
  - **Core**: `Core/src/application/` y `Core/src/domain/` (plano) estaban completamente vacíos en git — el layout `services/` era la única implementación real. Fix mecánico y seguro: `git mv` de todo `Core/src/services/application/*` → `Core/src/application/`, `Core/src/services/domain/*` → `Core/src/domain/` (sin tocar imports internos, que ya usaban `from domain import ...` esperando este layout), se borró `Core/src/services/` y se actualizó `Core/Dockerfile` para copiar `application/`/`domain/` en vez de `services/`.
  - **Auth**: acá había **dos implementaciones distintas** conviviendo. La plana (`Auth/src/application/auth_app_service.py` + `Auth/src/domain/services/auth/auth.py`, del trabajo de la sesión 2026-09-15 sobre `cambios-alejo`) tenía `register()` con `actor_id`/`contact_person`/`phone` y `get_me()`, pero **le faltaba por completo la emisión de tokens** (no existía ningún `TokenService`, ni `domain/__init__.py`) — nunca hubiera podido loguear a nadie. La anidada (`Auth/src/services/application/auth_app_service.py` + `services/domain/{token,user}/`) tenía la lógica completa y funcional de sesiones/tokens/permisos (`RefreshSession`, hash de tokens, `PermissionCompiler`, sync a Valkey) pero **no tenía** el `actor_id`/`contact_person`/`phone` en `register()` ni `get_me()`. Se **fusionaron**: se portaron esos dos agregados a la versión anidada (completa), agregando las excepciones que faltaban (`ActorNotFoundError`, `DefaultRoleDoesntExist`, `UserNotFound` en `services/domain/errors.py`), se borraron los archivos planos huérfanos e incompletos, se movió la versión anidada (ya fusionada) al layout plano vía `git mv`, y se actualizó `Auth/Dockerfile` igual que en `Core`.
  - Quedan como código muerto (no importado por ningún `__init__.py`, no rompen nada, pero es basura): `Core/src/application/alejo.py`, `Core/src/domain/services/alejo.py`, `Core/src/application/form_design.py` — mismo patrón de duplicados que ya se había limpiado en `cambios-alejo` mediante el trabajo de forms, pero nunca se propagó a `login-ch`.

Verificación: `python -m py_compile` sobre todos los archivos movidos/editados de `Auth` y `Core`, sin errores. **No se pudo levantar `docker compose` desde este entorno** (el `docker` CLI no está disponible en las herramientas de este agente — el usuario corre todo desde WSL); el diagnóstico y la corrección se hicieron leyendo código y logs pegados por el usuario, no ejecutando contenedores directamente. Falta que el usuario confirme con `docker compose build base && docker compose build auth core persister frontend && docker compose up -d` que ambos servicios arrancan limpio end-to-end.

---

## 2026-11-04 / 05 — Sesión: entorno local, registro de administrador, caída de `core` en producción y formularios persistidos en BD

Ramas involucradas: se empezó en `Dev`; el registro de administrador quedó en el commit `f214109` (ya desplegado); el trabajo de formularios está en **`formularios-response-db`** (sin commit al cierre de la sesión). Ojo: `formularios-response-db` parte de `1b172b1` y **no incluye** `f214109`.

### 1. Levantar el proyecto en local sin tocar lo versionado

Todo se resolvió con archivos ignorados por git, sin modificar `compose.yaml`:

- **Certificado HTTPS**: `compose.yaml` pide `Secrets/vd-cert.crt` / `vd-cert.key`, pero en `Secrets/` estaban como `cert.crt` / `cert.key` (mismo certificado, `CN=localhost`, vence 2027-05, la clave corresponde). Se copiaron con los nombres esperados.
- **Postgres no arrancaba**: `both POSTGRES_PASSWORD and POSTGRES_PASSWORD_FILE are set`. El `.env` local define `POSTGRES_PASSWORD` y `compose.yaml` pasa `POSTGRES_PASSWORD_FILE`. Se comentó la línea en `.env` (mismo valor que `Secrets/postgres_password`; `Packages/shared/.../postgres.py` cae al archivo si no hay variable). Respaldo en `Secrets/env.bak`.
- **`compose.override.yaml` local** (excluido vía `.git/info/exclude`, Docker lo carga solo):
  - publica el frontend en `4287:4287` (el commit `7331435` quitó ese mapeo de `compose.yaml` porque producción entra por nginx en `4290`);
  - usa un volumen nuevo **`iip_dev_pg`** para la BD: el volumen viejo `stats_vol_pg` tenía un esquema antiguo (sin `alembic_version`, sin `reference.system_roles`, `user_tiers` sin `code`) incompatible con el código actual. `stats_vol_pg` quedó intacto;
  - redefine los secretos a `./Secrets/...`: en git, `compose.yaml` usa las rutas del servidor (`/Secrets/...`), que no existen en local.
- BD nueva construida con el pipeline normal: `schemer → alembic upgrade head → seeder → populator`.
- **Usuario de prueba permanente**: `veeduria.admin` / `veeduria@admin.com`, tier `admin`, rol `admin`. Está en `Secrets/users.toml` (ignorado por git), así que el seeder lo recrea si se reconstruye la BD. Respaldo en `Secrets/users.toml.bak`.

### 2. Registro de administrador desde el login (commit `f214109`)

- Backend: `POST /public/auth/register-admin` (Auth). Crea el usuario con tier `admin` + rol `admin`, rechaza username o email repetido.
- Protegido por la variable **`ADMIN_REGISTRATION_KEY`** en `.env`: si está vacía o no existe, el endpoint responde `403 Admin registration is disabled.` (comportamiento esperado, no es un error). Si la clave no coincide: `403 INVALID_ADMIN_REGISTRATION_KEY`. Documentada vacía en `Secrets_Template/example.env`.
- Frontend: tercera pestaña **"Administrador"** en `LoginView.tsx` (usuario, nombre, correo, contraseña + confirmación, clave de registro).
- Producción: la variable se agrega a mano en el `.env` del servidor y se recrea `auth` (`docker compose up -d --no-deps --force-recreate auth`). Recomendado vaciarla de nuevo cuando ya no se necesite.

### 3. 502 en producción: `core` caído por imagen `base` desactualizada

Síntoma: `GET /api/core/public/parameters` → `502 Bad Gateway` (y todo `core`). Log: `ImportError: cannot import name 'UserFormAssignment' from 'shared.models'`.

Causa: `Auth`/`Core`/`Persistence` parten de `labcapital/apps:app-base`, que es donde se instala `Packages/shared` (los modelos). El workflow `.github/workflows/deploy-production.yml` solo hace `docker compose up -d --build --no-deps auth core frontend nginx`: **nunca reconstruye `base` ni corre migraciones**. Cuando cambia `shared`, `core` se construye con código nuevo sobre modelos viejos y se cae al importar. Además `auth` y `core` no tienen `restart: unless-stopped`, así que quedan caídos.

Arreglado a mano en el servidor (`docker compose build base` + rebuild de `auth core`). **Sigue pendiente arreglar el workflow** (ver Pendientes).

### 4. Formularios guardados y leídos desde la BD (rama `formularios-response-db`)

Problema reportado: "lo que guardo no aparece en incógnito ni en otro dispositivo". Causa: `AppContext.tsx` guardaba casi todo en `localStorage`. Diagnóstico por entidad:

| Dato | Antes | Ahora |
|---|---|---|
| Entidades / segmentos | BD (OK) | sin cambios |
| **Formularios** | se guardaban en BD pero la lista se leía de `localStorage`; borrar/duplicar solo local | **BD** (este cambio) |
| Usuarios de entidad | solo `localStorage` | **pendiente** |
| Asignaciones | solo `localStorage` | **pendiente** |
| Envíos (lista del admin) | solo `localStorage` | **pendiente** |

Backend (Core):
- `GET /public/forms` → lista (`ResponseFormSummary`, incluye `has_submissions`), más recientes primero.
- `GET /public/forms/{form_id}` → árbol completo (`ResponseFormTree`): mismo formato que el cuerpo de `POST /forms`, con ids. Reconstruye `depends_on` desde `rules.field_dependencies` y las reglas de archivo (`file_types`, `max_file_size`) desde `rules.field_rules`. Las secciones se cargan en plano con `selectinload` y se anidan por `parent_id` (ojo: `form.sections` trae también las hijas).
- `DELETE /public/forms/{form_id}` → solo admin (`403 FORM_FORBIDDEN_ERROR`), `409 FORM_HAS_SUBMISSIONS_ERROR` si tiene respuestas; borra preguntas → secciones → formulario (las asignaciones caen por `ON DELETE CASCADE`).
- Nuevas columnas `forms.forms.year`, `version`, `is_active` (antes la vigencia/versión/estado del constructor no se guardaban en ningún lado). Migración **`8e4f2a5b0d43_form_metadata`** (después de `7d3e1f4a9c32`); para formularios existentes con código de 4 dígitos, `year = code`.

Frontend:
- `utils/formTree.ts`: `fromFormTree()` (árbol del backend → `IIPForm`), inverso exacto de `toCreateFormRequest()`, que ahora también envía `year`/`version`/`is_active`.
- `services/coreService.ts`: `listForms()`, `getForm()`, `deleteForm()`.
- `context/AppContext.tsx`: los formularios se cargan del servidor en `refreshData()` al iniciar sesión. Tras guardar se **vuelve a leer** el formulario del servidor (un `PUT` reconstruye el árbol y cambian los ids de preguntas/campos; las respuestas deben usar los nuevos). Borrar llama al backend; duplicar guarda la copia en el servidor. En `localStorage` quedan **solo borradores nunca guardados** (`is_synced_to_backend = false`, clave `iip_all_forms`) y el id del formulario seleccionado (`iip_active_form_id`).
- `FormsManager.tsx`: al abrir el editor se carga la última versión del servidor; mensajes de error al borrar/duplicar.

Verificado en local: round-trip `toCreateFormRequest → POST → GET → fromFormTree → toCreateFormRequest` **idéntico** (pregunta Sí/No + bucle dependiente + archivo + selección múltiple + numérica); los ids resultantes son UUID del servidor; DELETE probado (403 sin rol admin, 409 con respuestas, 204 admin, sin huérfanos). `tsc --noEmit` limpio. **No probado haciendo clics en el navegador.**

**Despliegue de esta rama en producción (en este orden, si no `core` se cae como en §3):**

```bash
docker compose build base persister
docker compose run --rm --no-deps persister sh -c "cd /api/migrator && alembic upgrade head"
docker compose up -d --build --no-deps auth core frontend
```

---

## 2026-11-05 — Usuarios de entidad en la BD

Antes `createEntityUser` / `updateEntityUser` / `deleteEntityUser` solo tocaban `localStorage` (`iip_all_users`): la cuenta no existía en el servidor y no se veía desde otro navegador.

Backend (`Auth`), todos **solo administradores** (`403 ADMIN_REQUIRED_ERROR`; el rol se consulta en BD en cada llamada):
- `GET /public/auth/users` → lista con rol, entidad (`actor_id`, `actor_label`, segmento), contacto y estado.
- `PUT /public/auth/users/{id}` → `is_active`, `contact_person`, `phone` (solo lo enviado).
- `DELETE /public/auth/users/{id}` → 204; `400 INVALID_USER_OPERATION` si el admin intenta borrarse a sí mismo; `404` si no existe. Las asignaciones, vínculos y sesiones caen por `ON DELETE CASCADE`.
- Crear sigue siendo `POST /auth/register` (ya aceptaba `actor_id`, contacto y teléfono).

Frontend: `authService.listUsers/updateUser/deleteUser`; `AppContext` carga los usuarios en `refreshData()` si el usuario es admin, y tras `register` relee la lista para obtener el id real. `iip_all_users` ya no existe en `localStorage`. `EntityUsersManager` muestra el error del servidor si falla activar/desactivar/borrar.

Verificado: 403 con usuario normal; con admin → listar, crear, desactivar (el login del desactivado da 403), editar teléfono, borrar (204), borrar de nuevo (404), auto-borrado (400). `tsc --noEmit` limpio. **No probado con clics en el navegador.**

Gap conocido: borrar un usuario con filas en `audit.logs` o `interactions.comments` (FK sin cascada) fallaría con 500.

Despliegue: reconstruir `base` y `auth` (`docker compose build base auth && docker compose up -d --no-deps auth frontend`); no hay migración.

---

## 2026-11-05 — Asignaciones en la BD

Antes `createAssignment` / `batchAssignForm` / `removeAssignment` solo tocaban `localStorage` (`iip_assignments`); el backend ya tenía `POST /forms/assignments` y `GET /forms/assignments/me`, pero el admin nunca los usaba para listar.

Backend (`Core`), solo administradores (`403 FORM_ERROR` para el resto):
- `GET /public/forms/assignments` → todas las asignaciones con usuario, entidad, segmento, formulario, estado y avance (el avance se **calcula** del radicado de la entidad: sin radicado = pendiente, borrador = 50 %, enviado = 100 %).
- `DELETE /public/forms/assignments/{id}` → 204; `404` si no existe.
- `POST` (ya existía) crea o actualiza fecha/notas si ya existía esa pareja usuario-formulario.
- Se extrajeron `_require_admin` y `_progress` en `AssignmentAppService` (lo usan `assign`, `list_all` y `list_for_user`).

Frontend: `coreService.listAssignments/assignForm/deleteAssignment`. `AppContext` carga las asignaciones en `refreshData()` (admin: todas; entidad: `/assignments/me`, mapeadas a `FormAssignment` para que `EntityDashboard` siga funcionando). Crear, asignación masiva y revocar llaman al servidor y releen; `iip_assignments` ya no existe en `localStorage`. "Asignar formulario al crear usuario" ahora también se guarda en el servidor. La fecha límite se manda solo como `YYYY-MM-DD`. `batchAssignForm` usa `allSettled` y avisa cuántos fallaron.

Ojo: un formulario que sea solo borrador local (id `form-iip-…`, no guardado) no se puede asignar: hay que guardarlo primero.
`updateAssignmentProgress` / `completeAssignmentSubmission` quedan como actualización en memoria; el estado real lo calcula el servidor al recargar.

Verificado en local: entidad recibe 403 al listar/borrar; admin asigna (201), lista, revoca (204), revocar de nuevo (404); `/assignments/me` de la entidad sigue funcionando tras el refactor. `tsc --noEmit` limpio. **No probado con clics en el navegador.**

Despliegue: reconstruir `base` y `core` (`docker compose build base core && docker compose up -d --no-deps core frontend`); sin migración.

---

## Pendientes / gaps conocidos (no resueltos en esta sesión)

Cosas encontradas durante la revisión que quedan documentadas para no perderlas de vista:

- **Siguiente paso acordado — persistir el resto del admin en BD** (mismo problema que tenían los formularios, ver sesión 2026-11-04 §4):
  - ~~**Usuarios de entidad**~~ (resuelto 2026-11-05): `createEntityUser` / `updateEntityUser` / `deleteEntityUser` en `AppContext.tsx` solo tocan `localStorage`. Crear puede usar el `POST /auth/register` existente (ya acepta `actor_id`); falta un endpoint para listarlos (y editar/desactivar).
  - ~~**Asignaciones**~~ (resuelto 2026-11-05): `createAssignment` / `batchAssignForm` / `removeAssignment` / `updateAssignmentProgress` son locales. Existe `POST /forms/assignments` y `GET /forms/assignments/me`; faltan listar (admin) y eliminar.
  - **Envíos**: las respuestas sí se mandan (`POST /submissions/forms/{id}`), pero la lista que ve el admin (`submissions`, `addSubmission`, `updateSubmissionStatus`) es local; falta endpoint de listado.
  - Al terminar, en `localStorage` debería quedar solo el borrador de respuestas en curso (`FormSubmissionContext`).
- **Workflow de despliegue** (`.github/workflows/deploy-production.yml`): debe reconstruir `base` antes que `auth`/`core`, correr `alembic upgrade head`, y conviene agregar `restart: unless-stopped` a `auth` y `core` en `compose.yaml`. Causa directa del 502 de la sesión 2026-11-04 §3.
- **Datos del populator incompletos**: 6 scripts fallan (`11a_seed_section_types`: UUID no v7; `11g_seed_card_templates` / `11g_seed_field_groups`: dependencias faltantes; `12a`/`12b`: `load_instrument` no existe; `13a_seed_grading_criteria`: columnas `Bucle 2019`/`Pregunta 2019` faltantes en la hoja). Resultado: los formularios 2019–2027 se crean **sin preguntas**, y `15a_seed_submissions` no encuentra varias entidades.
- **`Scripts/launcher.sh` (restaurar backup)**: usa `${POSTGRES_PASSWORD}` dentro del contenedor `db`; si en `.env` solo existe `POSTGRES_PASSWORD_FILE` (como en el local actual), la restauración puede fallar por contraseña.
- **BD de producción**: confirmar con `alembic current` que está bajo alembic antes de correr `upgrade head` (el volumen viejo `stats_vol_pg` del local no lo estaba).
- **Plantilla de ejemplo**: si el servidor no tiene formularios, la vista de detalle muestra `IIP_DEFAULT_FORM` (del código) como antes; no es un dato real.
- **`.gitattributes` / CRLF**: muchos archivos aparecen modificados en `git status` solo por finales de línea; falta `git add --renormalize .` en un commit aparte.

- **Sin autorización granular en `Core`**: los routers de `Core` (`/actors`, `/forms`, `/submissions`) solo validan que el JWT sea válido, no qué puede hacer ese usuario (RBAC/ReBAC compilado en Valkey al login, pero nunca consultado después).
- **Gap 500 vs 401**: un token inválido/expirado en un endpoint protegido de `Core` responde `500` en vez de `401`, porque las excepciones de `shared/utils/tokens/errors.py` no heredan de `BaseDomainError`. No afecta a login/register (no requieren token), pero sí a todo lo demás.
- **`POST /submissions/forms/{form_id}`**: body sin tipar (`List[Any]`), con bugs conocidos — `AnswerFile` espera `value_id` pero el factory intenta `value`; los discriminadores `"multichoice"`/`"singlechoice"` no coinciden con los `code` reales de `reference.field_types` (`multi_choice`/`single_choice`); `"multichoice"` crea una respuesta vacía sin guardar nada.
- ~~**No hay `GET /forms` (listar) ni `GET /forms/{id}`**~~ — resuelto en la sesión 2026-11-04 §4 (rama `formularios-response-db`).
- **`Result.final_score`**: no se encontró lógica de agregación/ponderación implementada (`Criterion.weight` existe pero nada la usa).
- **`grading.Assignment` y `forms.Information`**: declaradas como referencia de tabla en `targets.py`, sin modelo ORM ni migración.
- **`persister` (Docker) no tiene `CMD`**: se opera solo vía `Scripts/launcher.sh` (`--setup`, `--schemer`, `--migrator`, `--seeder`, `--populator`). Si alguien intenta `docker compose up persister` esperando que corra solo, no pasa nada.
- **Tokens de GitHub en `Secrets/`**: son placeholders (mismo valor que `POSTGRES_PASSWORD`), no PATs reales. No hay código que los use hoy, pero si se activa el seeding vía GitHub habrá que reemplazarlos.
- **Selector de "entidad" en el registro del frontend**: el backend ahora sí soporta `actor_id` en el registro (ver §6), pero el campo `actor_label` que manda el frontend se ignora (es solo para mostrarlo en la UI) — no hace falta cambiar nada, es el comportamiento esperado.
