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

## Pendientes / gaps conocidos (no resueltos en esta sesión)

Cosas encontradas durante la revisión que quedan documentadas para no perderlas de vista:

- **Sin autorización granular en `Core`**: los routers de `Core` (`/actors`, `/forms`, `/submissions`) solo validan que el JWT sea válido, no qué puede hacer ese usuario (RBAC/ReBAC compilado en Valkey al login, pero nunca consultado después).
- **Gap 500 vs 401**: un token inválido/expirado en un endpoint protegido de `Core` responde `500` en vez de `401`, porque las excepciones de `shared/utils/tokens/errors.py` no heredan de `BaseDomainError`. No afecta a login/register (no requieren token), pero sí a todo lo demás.
- **`POST /submissions/forms/{form_id}`**: body sin tipar (`List[Any]`), con bugs conocidos — `AnswerFile` espera `value_id` pero el factory intenta `value`; los discriminadores `"multichoice"`/`"singlechoice"` no coinciden con los `code` reales de `reference.field_types` (`multi_choice`/`single_choice`); `"multichoice"` crea una respuesta vacía sin guardar nada.
- **No hay `GET /forms` (listar) ni `GET /forms/{id}`**: solo creación. El frontend no puede traer formularios existentes desde el backend real todavía.
- **`Result.final_score`**: no se encontró lógica de agregación/ponderación implementada (`Criterion.weight` existe pero nada la usa).
- **`grading.Assignment` y `forms.Information`**: declaradas como referencia de tabla en `targets.py`, sin modelo ORM ni migración.
- **`persister` (Docker) no tiene `CMD`**: se opera solo vía `Scripts/launcher.sh` (`--setup`, `--schemer`, `--migrator`, `--seeder`, `--populator`). Si alguien intenta `docker compose up persister` esperando que corra solo, no pasa nada.
- **Tokens de GitHub en `Secrets/`**: son placeholders (mismo valor que `POSTGRES_PASSWORD`), no PATs reales. No hay código que los use hoy, pero si se activa el seeding vía GitHub habrá que reemplazarlos.
- **Selector de "entidad" en el registro del frontend**: el backend ahora sí soporta `actor_id` en el registro (ver §6), pero el campo `actor_label` que manda el frontend se ignora (es solo para mostrarlo en la UI) — no hace falta cambiar nada, es el comportamiento esperado.
