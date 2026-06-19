# IIP Platform Monorepo

Welcome to the **IIP** monorepo. This repository contains a multi-service, domain-driven Python architecture managed with modern tooling like **Nix**, **uv**, and **Docker Compose**. The project is split into distinct services (`Auth`, `Core`, `Persistence`) backed by a unified `shared` package containing core business entities, data models, and utilities.

---

## 📂 Repository Architecture

The codebase follows **Domain-Driven Design (DDD)** principles and a clean architecture layout. Below is a breakdown of the primary directories:

```text
.
├── Auth/               # Authentication & Authorization Microservice
├── Core/               # Core Platform Microservice (Forms, Submissions, Grading)
├── Packages/shared/    # Shared library (DB engines, shared schemas, models, utilities)
├── Persistence/        # DB Migrations (Alembic), Seed data processors, and data loaders
├── Scripts/            # Shell utilities for orchestrating application launches
├── Secrets/            # Git-ignored local development credentials and certificates
└── compose.yaml        # Local multi-service orchestration layer

```

### Core Services Breakdown

- **`Auth` Service**: Handles identity management, token distribution, file storage records, and role-based access control.
- **`Core` Service**: Implements the main business domain—dynamic form structures, submission logic, rule dependencies, and automated evaluation/grading systems.
- **`Packages/shared`**: A local python package shared across `Auth` and `Core` to eliminate duplicate model definitions. Includes shared database connection engines, central enums, global Pydantic schemas, and security engines (JWT, Fernet encryption, Argon2 hashing).
- **`Persistence`**: Dedicated environment containing **Alembic** migrations (`migrator`), structural spreadsheet parsing loaders (`populator`), and raw schema seeds (`seeder`).

---

## 🛠️ Tech Stack & Tooling

- **Language Runtime:** Python 3.12.13
- **Package Management:** [uv](https://github.com/astral-sh/uv) (utilizing `uv.lock` and workspace-driven `pyproject.toml`)
- **Environment Isolation:** [Nix Flakes](https://nixos.wiki/wiki/Flakes) (`flake.nix` for deterministic development tools)
- **Gateway / Proxy:** Nginx (`nginx.conf`)
- **Database Tooling:** Alembic (Migrations) + SQLAlchemy (Data Mapping Models)
- **Containerization:** Docker & Docker Compose

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have the following tools installed locally:

- Docker & Docker Compose
- _Optional but highly recommended:_ Nix package manager (with flake support enabled) or Python 3.12+ with `uv` installed.

### 2. Environment & Secrets Configuration

Before initializing the applications, populate your cryptographic keys and environmental configuration blocks:

1. Copy the layout template to create your secrets baseline:

```bash
cp -r Secrets_Template/* Secrets/

```

2. Generate or fill in the required cryptographic files inside `./Secrets`:

- `jwt_private.pem` & `jwt_public.pem` (For asymmetric Auth tokens)
- `fernet_password` (For field-level data-at-rest encryption)
- `postgres_password` (Database root password)

### 3. Pure-Nix Development Environment (Alternative)

If you use Nix, drop straight into a pre-configured shell containing Python 3.12, `uv`, and system dependencies by running:

```bash
nix develop
# or if using direnv
direnv allow

```

---

## 🐳 Docker Deployment & Orchestration

The platform relies on a base context orchestration setup alongside service-specific overlays.

### Running the Infrastructure Stack

To spin up all microservices, database backends, and the Nginx reverse proxy simultaneously:

```bash
docker compose up --build

```

### Service-Specific Launchers

You can execute automated configuration wrappers explicitly via the provided launcher scripts:

```bash
chmod +x Scripts/launcher.sh Scripts/secrets.sh
./Scripts/launcher.sh

```

---

## 🗄️ Database Migrations & Data Seeding

Database management operations reside entirely inside the `Persistence/` workspace block.

### Running Database Migrations

Migrations automatically map database states using SQLAlchemy models imported out of the `shared` module:

```bash
cd Persistence
uv run alembic upgrade head

```

### Executing Database Seeders & Populators

The project incorporates a robust, staged pipeline for loading initial lookup types and structural layout schemas (e.g., parsing `Estructura_IIP.xlsx` and template CSVs):

- **Static Type Seeds** (`00a_...` to `33b_...`): System reference metrics (e.g., file types, operational rules, system roles).
- **Domain Structural Populators** (`10a_...` to `13a_...`): Dynamic form layouts, field constraints, sectors, and grading criteria templates.

To parse dynamic structures and apply all seed maps sequentially, run the following sequence:

```bash
cd Persistence/src
uv run populator/populator.py
uv run seeder/seeder.py

```
