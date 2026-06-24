#import "@preview/charged-vde:1.0.0": charged-vde
#import "@preview/cetz:0.3.1"
#import "@preview/merman:0.1.0": mermaid

#let note(content) = block(
  fill: rgb("e0f2fe"), inset: 10pt, radius: 4pt, stroke: rgb("38bdf8"), width: 100%,
  [#text(weight: "bold", fill: rgb("0369a1"))[ℹ️ Nota:] #content]
)
#let warning(content) = block(
  fill: rgb("fef2f2"), inset: 10pt, radius: 4pt, stroke: rgb("fca5a5"), width: 100%,
  [#text(weight: "bold", fill: rgb("b91c1c"))[⚠️ Atención:] #content]
)

#show raw.where(block: true): it => block(
  fill: luma(230),
  inset: 10pt,
  radius: 5pt,
  width: 100%,
  stroke: (left: 2pt + gray),
  it,
)

#show raw.where(block: false): it => box(
  fill: luma(230),
  inset: (x: 3pt, y: 0pt),
  outset: (y: 3pt),
  radius: 3pt,
  it,
)

#show: charged-vde.with(
  title: text(size: 28pt, weight: "bold")[Arquitectura y Especificaciones de la Plataforma IIP],
  authors: (
    (name: "Juan José Martínez Guerrero", affiliation: "1,2"),
  ),
  affiliations: (
    (id: "1", name: "Diseñador Industrial"),
    (id: "2", name: "Ingeniero de Sistemas"),
  ),
  email: [https://github.com/SpanishSyntax],
  lang: "es",
  abstract: [La plataforma del Índice de Innovación Pública (IIP) constituye un ecosistema de gestión de datos de alto rendimiento, diseñado como una arquitectura de microservicios orientada al dominio (DDD) para servir como el motor central de inteligencia y trazabilidad de la Veeduría Distrital. El sistema implementa una arquitectura basada en contenedores Docker que integra componentes especializados: autenticación, lógica central (Core), persistencia (Alembic/Seeders), almacenamiento persistente en PostgreSQL y un proxy inverso Nginx. Desarrollada bajo el patrón Fast API con capas de servicios, unidades de trabajo (UOW) y repositorios, la solución centraliza el ciclo de vida completo de las versiones 2019, 2021, 2023 y 2025 del IIP, abarcando desde la gestión de cuestionarios y respuestas hasta el procesamiento analítico de resultados. Esta infraestructura está diseñada como una solución escalable y abierta, preparada para la integración futura con motores de vectorización, sistemas de Generación Aumentada por Recuperación (RAG) y protocolos de Model Context Protocol (MCP), facilitando tanto la captura de nuevas propuestas y la gestión de procesos de evaluación, como la democratización de datos a través de portales de datos abiertos.],
)

= Introducción <intro>

La plataforma del índice de Innovación Pública (desde ahora IIP) se erige como un sofisticado ecosistema tecnológico, concebido como un hub de datos multidominio de alta disponibilidad, diseñado específicamente para satisfacer las necesidades analíticas y de gobernanza de la Veeduría Distrital. Este sistema no solo actúa como un repositorio centralizado, sino como un motor de procesamiento inteligente capaz de orquestar la complejidad inherente a los datos distritales, integrando de manera fluida la gestión dinámica de formularios, la administración de actores estratégicos y sistemas de evaluación robustos.

Bajo una arquitectura de microservicios estrictamente desacoplada, la plataforma garantiza una separación de responsabilidades que optimiza el ciclo de vida del software, permitiendo que los servicios de autenticación, la lógica de negocio central y la capa de persistencia operen como entidades independientes, aunque perfectamente cohesionadas. Todo este desarrollo está consolidado bajo una estrategia de monorepo, la cual permite la gestión unificada del código fuente, facilitando el intercambio de lógica a través de una biblioteca interna compartida. Esta infraestructura técnica, robusta y escalable, ha sido diseñada con una visión a largo plazo, garantizando que el sistema sea capaz de evolucionar desde una solución de gestión administrativa hacia un núcleo tecnológico preparado para la integración de sistemas de vectorización, arquitecturas RAG, y protocolos de comunicación de última generación como MCP, consolidándose así como la infraestructura de datos definitiva para la innovación pública.

== Propósito 

El propósito fundamental de la plataforma IIP es democratizar el acceso y la gestión del conocimiento derivado del Índice de Innovación Pública (IIP), funcionando como la columna vertebral de datos para la Veeduría Distrital. El alcance del sistema abarca la consolidación histórica y analítica de todas las versiones del índice (2019, 2021, 2023 y 2025), transformando una estructura de datos fragmentada en un modelo de información coherente, versionable y auditable.

En términos operativos, la plataforma está diseñada para satisfacer tres pilares críticos:

+ Gestión Integral del Ciclo de Vida: Desde la captura de nuevas respuestas y la gestión de actores, hasta la evaluación técnica realizada por el colegio calificador.

+ Interoperabilidad de Datos: Actuar como fuente única de verdad para la publicación de datos abiertos, facilitando el consumo analítico externo y asegurando la transparencia gubernamental.

+ Extensibilidad Inteligente: Servir como base de datos para sistemas avanzados, incluyendo la futura integración de servicios de RAG (Generación Aumentada por Recuperación) y agentes de IA, permitiendo consultas semánticas complejas sobre todo el histórico de resultados del IIP.

== Alcance

== Audiencia

== Vista panorámica

== Principios de diseño


== Mapa de arquitectura de alto nivel

#figure(
  mermaid(
    "
    graph TB
    subgraph Host_OS [Infraestructura / Host]
        subgraph Docker_Engine [Docker Engine]
            Nginx[Nginx Proxy]

            subgraph Services [Servicios en Ejecución]
                Auth[Auth Service]
                Core[Core Business Service]
            end

            subgraph Management [Contenedor de Gestión]
                Persistence[Persistence Service]
            end

            DB[(PostgreSQL Container)]
        end
    end

    Client((Usuario)) -->|HTTPS| Nginx
    Nginx -->|Route| Auth
    Nginx -->|Route| Core

    Auth -->|Auth/Roles| DB
    Core -->|Read/Write| DB

    Persistence -.->|Migraciones/Seeds/Backups| DB

    style Management stroke-dasharray: 5 5
    style Persistence fill:#f9f,stroke:#333
  ",
  ),
  caption: [Arquitectura de despliegue.],
) <dia-deploy>

El sistema se despliega mediante una arquitectura basada en contenedores Docker, orquestada para garantizar el aislamiento y la escalabilidad de cada componente. Un proxy inverso Nginx actúa como puerta de enlace, gestionando el enrutamiento del tráfico hacia los servicios correspondientes y asegurando una comunicación segura. La lógica interna sigue el patrón de diseño Domain-Driven Design (DDD), implementando una arquitectura de capas que organiza el código en servicios, unidades de trabajo (UOW) y repositorios, asegurando que la lógica de negocio permanezca desacoplada de los detalles técnicos de persistencia. Esta disposición permite una evolución independiente de cada módulo, desde la capa de autenticación hasta el motor de procesamiento de datos gestionado por el servicio de core y el motor de base de datos PostgreSQL.

= Arquitectura de sistema

La arquitectura de la plataforma IIP se fundamenta en un diseño modular de microservicios, orquestado mediante contenedores para garantizar la independencia, la escalabilidad horizontal y el aislamiento de responsabilidades. Hemos abandonado los enfoques monolíticos tradicionales en favor de una estructura de monorepo, la cual permite la gestión unificada del código fuente bajo una estrategia de workspace. Como se ilustra en @dia-deps, esta decisión estratégica facilita que los dominios funcionales (Auth, Core, Persistence) compartan una base común de utilidades y modelos (el módulo Shared), garantizando la consistencia del sistema y la reducción de la duplicidad de código sin sacrificar la independencia de despliegue de cada servicio.

Este modelo es ideal para las necesidades de la Veeduría Distrital, ya que permite una gobernanza centralizada del código mientras asegura una escalabilidad granular, facilitando ciclos de desarrollo independientes para los componentes de autenticación y lógica de negocio central.

#figure(
  mermaid(
    "
    graph BT
    subgraph Monorepo [Workspace: IIP Platform]
        direction BT
        Shared[Librería Compartida / Shared]

        Auth[Auth Service] -->|Importa tipos/utils| Shared
        Core[Core Service] -->|Importa tipos/utils| Shared
        Persistence[Persistence Service] -->|Importa tipos/utils| Shared
    end

    style Shared fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style Monorepo fill:#f5f5f5,stroke:#9e9e9e,stroke-dasharray: 5 5
  ",
  ),
  caption: [Dependencias de módulos dentro del monorepo.],
) <dia-deps>

== Stack tecnológico

El sistema está construido sobre un stack moderno orientado al rendimiento y la seguridad transaccional:

+ *Runtime:* Python 3.12.13
+ *Framework:* FastAPI
+ *ORM & DB:* SQLAlchemy 2.0 con PostgreSQL
+ *Migraciones:* Alembic
+ *gestión de paquetes:* uv with workspace support
+ *Seguridad:* Argon2 para hashing y ED25519 para JWT

Para un desglose detallado de las dependencias en materia de librerías del proyecto, por favor remítase a los `pyproject.toml` correspondientes a cada contenedor y al `pyproject.toml` global del proyecto.

#figure(
  table(
    columns: (auto, auto, auto),
    inset: 10pt,
    align: horizon,
    table.header([*Servicio*], [*Responsabilidad*], [*Entidades Clave*]),
    [Nginx], [Proxy inverso y enrutamiento], [Configuración, Certificados],
    [Auth], [Gestión de identidad y seguridad], [User, Role, RefreshSession],
    [Core],
    [Lógica de negocio y procesamiento de dominio],
    [Form, Submission, Actor, Grade],

    [Persistence],
    [Ciclo de vida de BD, migraciones y carga],
    [Alembic, Seeder, Populator],

    [Shared],
    [Lógica común, modelos ORM y utilidades],
    [Base, AccessContext, Hashing],
  ),
  caption: [Componentes del sistema y sus responsabilidades.],
  placement: bottom,
) <tab-comps>

= Arquitectura de despliegue

== Infraestructura

== Arquitectura Docker

== Proxy inverso

== Comunicación de servicios

== Variables de ambiente

== Secretos y contraseñas

= Arquitectura de dominio

== Microservicios

La lógica se encuentra particionada funcionalmente. El servicio Auth gestiona exclusivamente la identidad; el servicio Core encapsula la lógica de negocio del IIP, y el servicio de Persistence actúa como el motor de estado para Alembic y los seeders, asegurando que los datos históricos de 2019, 2021, 2023 y 2025 sean inyectados y mantenidos con integridad. Todo este despliegue está protegido por una capa de Nginx, tal como se detalla en @dia-deploy.



== DDD

El servicio Core implementa una arquitectura basada en Domain-Driven Design @book_ddd_evans2004 (DDD), organizada en capas que separan las responsabilidades de presentación, aplicación, dominio e infraestructura. Esta organización permite mantener la lógica de negocio desacoplada de los mecanismos de persistencia y comunicación, facilitando la mantenibilidad, la extensibilidad y las pruebas unitarias.

#figure(
  box(
    height: 10cm,
    mermaid(
      "
      graph TD

      API[Capa API / FastAPI]
      ORC[Servicio Orquestrador]
      SER[Servicio Especializado]
      UOW[Unidad de trabajo / UOW]
      REP[Repositorios]
      MOD[Modelos | ORM]
      DB[(PostgreSQL)]

      API --> ORC
      ORC --> SER
      SER --> UOW
      UOW --> REP
      REP --> MOD
      MOD --> DB
      ",
    ),
  ),
  caption: [Arquitectura de capas orientada al dominio (DDD).],
) <dia-capas>

+ *Capa API:* Expone los endpoints REST mediante FastAPI y actúa como punto de entrada al sistema. Su responsabilidad se limita a la validación de solicitudes, autenticación y serialización de respuestas.

+ *Servicio Orquestrador:* Coordina el flujo de ejecución de los casos de uso. Esta capa encapsula la lógica de alto nivel, delegando las operaciones específicas en servicios especializados sin contener reglas de negocio propias.

+ *Servicios Especializados:* Implementan la lógica de negocio asociada a cada dominio funcional, como la gestión de formularios, respuestas o auditorías. Estos servicios utilizan la Unidad de Trabajo para ejecutar operaciones transaccionales de forma consistente.

+ *Unidad de Trabajo y Repositorios:* La Unidad de Trabajo (UOW) administra el ciclo de vida de las transacciones y garantiza la atomicidad de las operaciones. Los repositorios abstraen el acceso a los datos, desacoplando la lógica de negocio de la tecnología de persistencia utilizada.

+ *Modelos ORM y Base de Datos:* La capa de persistencia emplea modelos definidos con SQLAlchemy ORM para mapear las entidades del dominio a la base de datos PostgreSQL, proporcionando una interfaz orientada a objetos sobre el almacenamiento relacional.

Esta separación de responsabilidades facilita la evolución independiente de cada capa, mejora la mantenibilidad del sistema y simplifica la implementación de pruebas unitarias al reducir el acoplamiento entre la lógica de negocio y la infraestructura.

== Arquitectura de capas

== Servicios

== Repositorios

== UOW

== Shared

= Arquitectura de datos

== Base de datos

  #figure(
  image("./images/db_arq.jpeg", width: 85%),
  caption: [Arquitectura de flujo y dependencias del sistema de persistencia.],
)

== Modelos


#grid(
  columns: (1fr),
  inset: 5pt,
  [
    ```text
    Packages/shared/src/shared/models
    ├── actors.py
    ├── audit.py
    ├── auth.py
    ├── files.py
    ├── forms.py
    ├── grading.py
    ├── __init__.py
    ├── interactions.py
    ├── links.py
    ├── reference.py
    ├── rules.py
    ├── submissions.py
    └── targets.py
    ```
  ]
)

== Relaciones

== Gestión

= Persistencia

== Creación de DB schemas

Este módulo automatiza la creación de esquemas de base de datos en PostgreSQL durante el despliegue inicial del sistema, inspeccionando dinámicamente las clases del modelo de datos para garantizar la existencia de las estructuras necesarias. El script de persistencia extrae de manera única los nombres de los esquemas definidos en la clase `TargetTable` y sus clases base mediante introspección de código, identificando cada atributo que implemente el tipo `TableInfo`. 

Posteriormente, abre una sesión síncrona con la base de datos y ejecuta de forma iterativa comandos seguros de creación de esquemas que previenen errores por duplicación. El flujo maneja de forma independiente cada confirmación o reversión ante fallos y genera un informe final en el registro del sistema detallando las estructuras creadas de manera exitosa y las fallidas.

El script `launcher.sh` ejecuta automáticamente este proceso de inicialización al detectar la bandera `--setup`, simplificando la configuración del entorno cuando el sistema se despliega por primera vez en un servidor virgen.

#note([Nota: La ejecución exitosa mediante la bandera `--setup` requiere que las credenciales y variables de entorno de la base de datos estén correctamente configuradas, y que el motor de PostgreSQL esté activo y aceptando conexiones.])

== Alembic

La configuración de Alembic permite gestionar el ciclo de vida de la base de datos, incluyendo la carga dinámica de modelos y la definición de una tabla personalizada para las migraciones, `alembic_automatic_version`. Para asegurar la persistencia y sincronización entre el host y el contenedor `app_persister`, el volumen de versiones de Alembic debe montarse en docker-compose, reflejando la estructura necesaria de archivos en `Persistence/src/migrator/alembic/versions`.

```yaml
  persister:
    ...
    volumes:
      # Huesped : Contenedor
      - "./Persistence/src/migrator/alembic/versions:/api/migrator/alembic/versions"
      # Cambie sólo la ruta en huésped, NO cambie ruta en contenedor.
```

El montaje del volumen de Alembic es obligatorio, y si el directorio versions en el host está vacío o no coincide con el estado actual de los modelos al levantar el servicio persister, las migraciones automáticas fallarán al no poder contrastar la metadata con el historial de revisiones previo.

== Poblado de sistema (`seeds`)

Este módulo automatiza la carga de datos maestros e iniciales (seeds) en la base de datos tras asegurar la existencia de los esquemas y aplicar las migraciones correspondientes. El mecanismo implementado en `seeder.py` escanea dinámicamente el directorio interno `seeds/`, ordenando alfabéticamente los archivos encontrados para garantizar una secuencia de ejecución predecible y respetar las dependencias relacionales subyacentes. Utilizando el módulo `importlib.util` de Python, el script realiza una carga reflexiva de cada archivo `.py`, busca de forma explícita una función ejecutable llamada `upgrade()` y la invoca de manera aislada dentro de un bloque controlado de excepciones. El flujo captura errores individuales por archivo para evitar que un fallo en un set de datos interrumpa todo el proceso de inicialización, generando un registro detallado en el `logger` y volcando la traza completa (`traceback`) en la consola ante cualquier eventualidad.

Al igual que los módulos previos de persistencia, este componente es invocado automáticamente por el script `launcher.sh` al ejecutar la bandera `--setup` durante el despliegue en un entorno virgen, asegurando que las tablas base queden completamente pobladas.

Para asegurar el correcto orden de inserción (por ejemplo, registrar roles antes que usuarios), el directorio debe mantener una nomenclatura secuencial estricta tal como se ilustra en la siguiente estructura física:

#grid(
  columns: (1fr),
  inset: 5pt,
  [
    ```text
    Persistence/src/seeder
    ├── seeder.py
    └── seeds
        ├── 00a_seed_log_action_types.py
        ├── 00b_seed_file_types.py
        ├── 00c_seed_roles.py
        ├── 00d_seed_user_tiers.py
        ├── 10a_seed_users.py
        ├── 1b_seed_rule_types.py
        ├── 1c_seed_relational_operators.py
        ├── 1f_seed_submission_status_types.py
        ├── 30a_seed_field_types.py
        ├── 33a_seed_notification_types.py
        ├── 33b_seed_comment_types.py
        └── __init__.py
    ```
  ]
)

#note([Nota: Cualquier script de inicialización nuevo que se añada a la carpeta `seeds/` debe implementar obligatoriamente la función `upgrade()`. Se recomienda seguir el patrón numérico/alfabético prefijado (`00a_`, `10a_`) para controlar de forma explícita el orden de carga y evitar fallos por restricciones de llave foránea en la base de datos.])

== Poblado de históricos (`populator`)

Este componente gestiona la ingesta masiva de datos históricos y estructuras complejas en el sistema a través de la API pública de los microservicios, en lugar de realizar inserciones directas en el motor de persistencia. El módulo se orquesta de manera asíncrona mediante `asyncio` y `httpx`, conectándose con el servicio de autenticación (`api_auth`) y el núcleo del sistema (`api_core`) utilizando variables de entorno para resolver los endpoints internos de la red de Docker. El flujo extrae las credenciales iniciales de un archivo TOML administrado mediante secretos de Docker (`/run/secrets/users_file`), priorizando cuentas de nivel `root` para autenticarse, obtener el token Bearer correspondiente e inyectarlo automáticamente en las cabeceras de las peticiones. Para mitigar fallas en tareas de larga duración, la capa del cliente (`ServiceClient`) implementa mecanismos de re-autenticación automática que refrescan el token de acceso si este expira a mitad de una transacción.

La extracción de la data histórica se delega a un conector dedicado (`GitHubConnector`) que descarga los conjuntos de datos crudos o estructuras estructuradas directamente desde repositorios remotos utilizando un token de acceso seguro provisto como secreto de Docker (`/run/secrets/github_token_seeds`). Cada registro recuperado pasa por una capa estricta de validación local mediante esquemas de Pydantic antes de despacharse hacia la API pública de `api_core`. La transferencia de datos se realiza tanto en registros individuales como en procesamiento por lotes que comparten el mismo grupo de conexiones para optimizar el rendimiento. Al procesar las solicitudes mediante peticiones HTTP estándar (`POST`), el sistema garantiza que toda la lógica de negocio, validaciones relacionales y disparadores de eventos del backend se apliquen correctamente a la data histórica, tal como ocurriría con la interacción regular de un usuario.

La estructura física del módulo organiza las tareas en el directorio `pops/` de forma secuencial, incluyendo scripts específicos de migración y plantillas locales en formatos estructurados (CSV y XLSX) dentro de subdirectorios de trabajo:

#grid(
  columns: (1fr),
  inset: 5pt,
  [
    ```text
    Persistence/src/populator
    ├── pops
    │   ├── 10a_seed_sectors.py
    │   ├── 10b_seed_entities.py
    │   ├── 11a_seed_section_types.py
    │   ├── 11b_seed_forms.py
    │   ├── 11c_seed_sections.py
    │   ├── 11d_seed_questions.py
    │   ├── 11e_seed_loop_questions.py
    │   ├── 11f_seed_card_templates.py
    │   ├── 11g_seed_field_groups.py
    │   ├── 11h_seed_fields.py
    │   ├── 11i_seed_field_choices.py
    │   ├── 12a_seed_field_dependencies.py
    │   ├── 12b_seed_field_rules.py
    │   ├── 13a_seed_grading_criteria.py
    │   ├── __init__.py
    │   └── jhonatan
    │       ├── actors.actor_segments_template.csv
    │       ├── actors.actors_template.csv
    │       ├── Entidades.csv
    │       └── Estructura_IIP.xlsx
    └── populator.py
    ```
  ]
)

#note([Nota: A diferencia de los módulos de esquemas, migraciones y datos maestros, el proceso de población masiva histórica no se ejecuta de forma mandatoria con la bandera `--setup` en sistemas limpios si los secretos o conectores externos de GitHub no están mapeados. Este componente requiere que tanto el contenedor de autenticación como el servicio núcleo estén completamente activos, saludables y con la base de datos ya estructurada.])


== Backup y Restore

Este sistema gestiona los respaldos de la base de datos PostgreSQL mediante un volumen en Docker Compose que vincula el directorio local `./Persistence/src/backups` con la ruta interna `/backups` del servicio `persister`.

```yaml
  persister:
    ...
    volumes:
      - "./Persistence/src/backups:/backups"
```

La administración se automatiza a través del script `launcher.sh` empleando dos banderas principales: `--backup`, que ejecuta de forma no interactiva un `pg_dump` nombrando el archivo con una marca de tiempo para evitar sobrescrituras, y `--restore`, que requiere el nombre del archivo `.sql` como argumento e inyecta la variable `PGPASSWORD` internamente para autenticar de manera automática la restauración mediante `psql`.

Dado que el proceso de restauración sobrescribe los datos actuales de la base de datos, se recomienda ejecutar un respaldo preventivo antes de realizar cualquier importación.



#note([Nota: Se debe asegurar que el directorio local `./Persistence/src/backups` cuente con los permisos de lectura y escritura correctos para que el contenedor pueda almacenar los archivos.])

La gestión de respaldos se centraliza en el script de automatización utilizando las siguientes banderas:

=== Crear un Respaldo (`--backup`)

Genera una copia de seguridad en caliente de la base de datos PostgreSQL utilizando la herramienta pg_dump. El comando se ejecuta de forma no interactiva (-T) y almacena el archivo resultante usando una marca de tiempo (`TIMESTAMP`) para evitar la sobrescritura de respaldos anteriores.

```bash
  --backup)
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="./Persistence/src/backups"

    mkdir -p "$BACKUP_DIR"

    echo "Creating database backup inside $BACKUP_DIR..."

    if docker compose exec -T db sh -c "pg_dump -U \"${USER_VAR}\" -d \"${DB_VAR}\" > /backups/db_backup_$TIMESTAMP.sql"; then
      echo "✅ Backup completed successfully: $BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    else
      echo "❌ Backup failed."
    fi
    ;;
```

=== Restaurar un Respaldo (`--restore`)

Permite restaurar un archivo .sql específico cargándolo directamente en el motor de la base de datos mediante psql. El script requiere el nombre del archivo como parámetro e inyecta la variable `PGPASSWORD` de forma interna para realizar la autenticación automática sin solicitar credenciales en la terminal.

```bash
  --restore)
    INPUT_FILE="${1:-}"
    if [ -z "$INPUT_FILE" ]; then
      echo "Usage: ./launcher.sh --restore <backup_filename.sql or path>"
      echo "Example: ./launcher.sh --restore db_backup_20260618_232418.sql"
      exit 1
    fi

    FILE_NAME=$(basename "$INPUT_FILE")

    echo "Restoring database from $FILE_NAME..."

    # Inject PGPASSWORD so Postgres authenticates automatically without prompting
    if docker compose exec -T db sh -c "PGPASSWORD=\"\${POSTGRES_PASSWORD}\" psql -h db -U \"${USER_VAR}\" -d \"${DB_VAR}\" < /backups/$FILE_NAME"; then
      echo "✅ Restore completed successfully."
    else
      echo "❌ Restore failed. Make sure $FILE_NAME exists in your backups directory."
    fi
    ;;
```



= autenticación y Autorización

== Servicio de autenticación

== autenticación JWT

== Roles y permisos

== Sesiones de refresco

== Seguridad de contraseñas

= Arquitectura de API



== Flujo de Datos

El flujo de información es transaccional y validado. Cuando un cliente solicita una operación, el tráfico es enrutado por Nginx hacia el servicio correspondiente tras validar el contexto de seguridad. La secuencia operativa típica, donde el servicio Core interactúa con PostgreSQL mediante los repositorios DDD, se describe en @dia-flujo. Este diseño asegura que cada petición sea trazable, consistente y eficiente, permitiendo que la plataforma soporte tanto la carga administrativa actual como las futuras demandas de analítica avanzada.

#figure(
  mermaid(
    "
    sequenceDiagram
    participant U as Usuario/Cliente
    participant N as Nginx Proxy
    participant A as Auth Service
    participant C as Core Service
    participant D as PostgreSQL

    U->>N: Request (JWT Auth)
    N->>A: Validar Token
    A-->>N: Autorizado
    N->>C: Procesar Lógica de Negocio
    C->>D: Consultar Datos
    D-->>C: Resultado
    C-->>N: Response (JSON)
    N-->>U: 200 OK
  ",
  ),
  caption: [Diagrama de secuencia del flujo de una petición API.],
) <dia-flujo>

= Configuración y Despliegue

== Requisitos previos

== Configuración de Docker Compose

== Gestión de variables de entorno y secretos

= Arquitectura de Datos y Persistencia

== Diseño del modelo relacional

== Estrategia de migraciones

== Separación por esquemas

== Seedeo de iniciales

== Seedeo de históricos

= API y Endpoints

== Documentación de la API

== Estándares de comunicación y seguridad

= Desarrollo y Utilidades

== Estructura de directorios del monorepo

== Uso de utilidades Python internas.

== Guía de contribución y estilo de código.

= Hoja de Ruta (Roadmap) y Futuras Integraciones

== Implementación de Celery Workers para procesos en segundo plano.

== Integración de sistemas de Vectorización y RAG.

== Implementación de servidores MCP para agentes de IA.

= Apéndice y Glosario

= Eraser

= Table of Contents

1. Introduction
   Purpose
   Scope
   Intended Audience
   Platform Overview
   Design Principles

2. System Architecture
   High-Level Architecture
   Architectural Decisions
   Service Overview
   Monorepo Structure
   Technology Stack

3. Deployment Architecture
   Infrastructure Overview
   Docker Architecture
   Reverse Proxy (Nginx)
   Service Communication
   Configuration Management
   Environment Variables
   Secrets Management

4. Domain Architecture
   Domain-Driven Design
   Layered Architecture
   Application Services
   Repositories
   Unit of Work
   Shared Library
   Request Lifecycle

5. Data Architecture
   Database Overview
   Schema Organization
   Domain Entities
   Relationships
   Historical IIP Versions
   Data Integrity
   Auditability

6. Persistence
   SQLAlchemy
   Alembic Migrations
   Seeders
   Historical Data Population
   Backup and Recovery

7. Authentication & Authorization
   Authentication Service
   JWT Authentication
   Roles & Permissions
   Refresh Sessions
   Password Security

8. API Design
   REST Conventions
   API Structure
   Authentication Flow
   Error Handling
   Pagination & Filtering
   OpenAPI Documentation

9. Development Guide
   Repository Structure
   Workspace Management
   Dependency Management
   Local Development
   Testing
   Code Style
   Contributing

10. Operations
   Deployment
   Logging
   Monitoring
   Performance
   Maintenance

11. Future Evolution
   Background Workers
   Open Data Integration
   Semantic Search
   Vector Database Integration
   Retrieval-Augmented Generation (RAG)
   MCP Integration
12. Appendix
   Directory Structure
   Configuration Reference
   Glossary
   Acronyms


= 1. Introducción
== Propósito
== Alcance
== Audiencia destinada
== Visión general de la plataforma
== Principios de diseño

= 2. Arquitectura del sistema
== Arquitectura de alto nivel
== Decisiones arquitectónicas
== Visión general de los servicios
== Estructura de monorepo
== Stack tecnológico

= 3. Arquitectura de despliegue
== Visión general de la infraestructura
== Arquitectura Docker
== Proxy inverso (Nginx)
== Comunicación entre servicios
== Gestión de configuración
== Variables de entorno
== Gestión de secretos

= 4. Arquitectura de dominio
== Diseño guiado por el dominio (DDD)
== Arquitectura en capas
== Servicios de aplicación
== Repositorios
== Unidad de trabajo (Unit of Work)
== Librería compartida
== Ciclo de vida de la solicitud

= 5. Arquitectura de datos
== Visión general de la base de datos
== Organización del esquema
== Entidades de dominio
== Relaciones
== Versiones históricas de IIP
== Integridad de datos
== Auditoría

= 6. Persistencia
== SQLAlchemy
== Migraciones con Alembic
== Seeders
== Población de datos históricos
== Respaldo y recuperación

= 7. Autenticación y autorización
== Servicio de autenticación
== Autenticación JWT
== Roles y permisos
== Sesiones de refresco
== Seguridad de contraseñas

= 8. Diseño de API
== Convenciones REST
== Estructura de la API
== Flujo de autenticación
== Gestión de errores
== Paginación y filtrado
== Documentación OpenAPI

= 9. Guía de desarrollo
== Estructura del repositorio
== Gestión de espacios de trabajo
== Gestión de dependencias
== Desarrollo local
== Pruebas
== Estilo de código
== Contribución

= 10. Operaciones
== Despliegue
== Registro (Logging)
== Monitoreo
== Rendimiento
== Mantenimiento

= 11. Evolución futura
== Trabajadores en segundo plano (Background Workers)
== Integración de datos abiertos
== Búsqueda semántica
== Integración de bases de datos vectoriales
== Generación aumentada por recuperación (RAG)
== Integración MCP

= 12. Apéndice
== Estructura de directorios
== Referencia de configuración
== Glosario
== Acrónimos

#bibliography("library.bib")



