# IIP Platform Monorepo

Welcome to the **IIP** monorepo. This repository contains a multi-service, domain-driven Python architecture managed with **Nix**, **uv**, and orchestrated via **Docker Compose**. The project is split into explicit services (`Auth`, `Core`, `Persistence`) backed by a local `shared` package containing unified business entities, data models, and core utilities.

---

## 📂 Repository Architecture

The codebase follows **Domain-Driven Design (DDD)** principles and a clean architecture layout:

```text
.
├── Auth/               # Authentication & Authorization Microservice
├── Core/               # Core Platform Microservice (Forms, Submissions, Grading)
├── Packages/shared/    # Shared library (DB engines, enums, models, schemas)
├── Persistence/        # DB Migrations (Alembic), Seed data processors, and data loaders
├── Scripts/            # Operations engineering scripts (Setup, Launchers, Secrets)
└── compose.yaml        # Local multi-service orchestration layer

```

### Core Services Breakdown

- **`Auth` Service**: Handles identity management, token generation, file storage records, and role-based access control.
- **`Core` Service**: Implements the primary business domain—dynamic form structures, submission logic, dependency rules, and evaluation/grading systems.
- **`Packages/shared`**: A local shared Python module used by both microservices to eliminate duplicate code. Houses core SQLAlchemy definitions, system-wide enums, global Pydantic schemas, and security/hashing layers.
- **`Persistence`**: Dedicated data architecture environment containing **Alembic** migrations (`migrator`), structural spreadsheet data parsers (`populator`), and reference data scripts (`seeder`).

---

## 🛠️ Tech Stack & Tooling

- **Language Runtime:** Python 3.12.13
- **Package Management:** [uv](https://github.com/astral-sh/uv) (utilizing workspace-driven dependencies)
- **Environment Isolation:** [Nix Flakes](https://nixos.wiki/wiki/Flakes) (`flake.nix` for deterministic development tools)
- **Gateway / Proxy:** Nginx (`nginx.conf`)
- **Database Pipeline:** Alembic + SQLAlchemy + PostgreSQL

---

## 🚀 Getting Started

Follow these steps in sequence to safely bootstrap your local development environment.

### 1. Generate Configuration & Certificates

The platform requires specific environment variables and cryptographic keypairs. Run the automated secrets generator script from within the `Scripts` directory:

```bash
cd Scripts
chmod +x secrets.sh launcher.sh
./secrets.sh

```

**What this script does:**

- Creates a root-level `.env` scaffolding file populated from the templates.
- Copies default operational user setups (`users.toml`) into your `./Secrets` directory.
- Automatically issues local self-signed testing certificates (`cert.crt` / `cert.key`) via `openssl` for secure local HTTPS termination.
- Generates an **ED25519 asymmetric key pair** (`jwt_private.pem` / `jwt_public.pem`) for cryptographic validation of authorization tokens.

> ⚠️ **Important:** Review and modify the newly created root `.env` and `./Secrets/users.toml` files to change any default passwords prior to launching services in a public environment.

### 2. Fast Setup & Initialization Pipeline

To stand up the database infrastructure, generate schemas, apply database migrations, and parse spreadsheet datasets in one unified command, use the setup engine tool:

```bash
./launcher.sh --setup

```

This automates the following steps under the hood:

1. Bootstraps the PostgreSQL instance container.
2. Code-checks and waits up to 60 seconds for active database responsiveness.
3. Generates global structural definitions using `schemer.py`.
4. Executes Alembic migrations (`upgrade head`).
5. Sequentially applies reference lookup values (`seeder.py`) and dynamic form configurations/metrics (`populator.py`).
6. Spins up remaining background system microservices automatically.

---

## 🎛️ Operations CLI Tool (`launcher.sh`)

The `launcher.sh` script acts as an administrative entrypoint for database maintenance and container cycles. Ensure you run commands from inside the `Scripts/` folder.

### Database Operations

| Command                                          | Description                                                                                                                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `./launcher.sh --setup`                          | Compiles architecture schemas, upgrades migrations, executes seed data loading pipelines, and starts application services.                                                           |
| `./launcher.sh --revision "your_migration_name"` | Compares your active SQLAlchemy definitions against the running database instance and autogenerates an Alembic migration script inside `Persistence/src/migrator/alembic/versions/`. |
| `./launcher.sh --extract`                        | Pulls existing structural spreadsheet profiles directly out of active database models.                                                                                               |
| `./launcher.sh --backup`                         | Performs a localized data dump of your core state into a timestamped file located in `./Backups/`.                                                                                   |
| `./launcher.sh --restore <path_to_backup.sql>`   | Streams raw structural `.sql` statements to quickly restore database state profiles.                                                                                                 |

---

## ❄️ Nix Integration (Optional)

If your host operating system utilizes Nix flakes, you can instantly load all native system dependencies (such as Python 3.12, `uv`, and `openssl` runtimes) by invoking:

```bash
nix develop
# or let direnv auto-load it when navigating code blocks
direnv allow

```
