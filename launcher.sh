# !usr/bin/env bash
set -eu

MODE="${1:-}"
shift || true

# Load environment variables from .env if present
if [ -f .env ]; then
    # Export all non-empty, non-comment lines
    export $(grep -vE '^(#|$)' .env | xargs)
else
    echo "⚠️  Warning: .env file not found, environment variables may be missing."
fi

case "$MODE" in
    # ===========================================
    #   Docker lifecycle commands
    # ===========================================
    --setup)
        MSG="${1:-default}"
        echo "🐘 Starting database container..."
        mkdir -p ../Secrets/jwt
        if [ ! -f ../Secrets/jwt/jwt_private.pem ]; then
            openssl genpkey -algorithm ED25519 -out ../Secrets/jwt/jwt_private.pem
            openssl pkey -in ../Secrets/jwt/jwt_private.pem -pubout -out ../Secrets/jwt/jwt_public.pem
        fi
        docker compose up -d db
        echo "⏳ Waiting for database readiness (max 60s)..."
        TIMEOUT=60
        SECONDS=0
        until docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
            sleep 1
            if [ $SECONDS -ge $TIMEOUT ]; then
                echo "❌ Database did not become ready after $TIMEOUT seconds."
                exit 1
            fi
            echo "   ...still waiting ($SECONDS s)"
        done
        echo "✅ Database is ready!"
        echo "1️⃣  Creating schemas..."
        docker compose run --rm persister sh -c "cd /api/schemer  && python schemer.py"
        echo "2️⃣  Applying migrations (upgrade head)..."
        docker compose run --rm persister sh -c "cd /api/migrator  && alembic upgrade head"
        echo "3️⃣  Seeding tables..."
        docker compose run --rm persister sh -c "cd /api/seeder && python seeder.py"
        echo "✅ Starting services..."
        docker compose up -d
        ;;

    --start | -s)
        echo "Starting containers..."
        docker compose up -d
        ;;

    --clean | -c)
        echo "Cleaning containers and volumes..."
        docker compose down -v
        ;;

    # ===========================================
    #   Database management
    # ===========================================
    --schema)
        MSG="${1:-default}"
        echo "1️⃣  Creating schemas..."
        docker compose run --rm api_auth sh -c "cd /api && python -m seed.seed_schema"
        ;;

    --generate)
        MSG="${1:-default}"
        echo "🐘 Starting database container..."
        docker compose up -d db
        echo "⏳ Waiting for database readiness (max 60s)..."
        TIMEOUT=60
        SECONDS=0
        until docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; do
            sleep 1
            if [ $SECONDS -ge $TIMEOUT ]; then
                echo "❌ Database did not become ready after $TIMEOUT seconds."
                exit 1
            fi
            echo "   ...still waiting ($SECONDS s)"
        done
        echo "1️⃣  Autogenerating Alembic revision: '$MSG'..."
        docker compose run --rm api_auth sh -c "cd /api && alembic revision --autogenerate -m \'$MSG\'"
        ;;
    
    --create-keys)
        echo "1️⃣  Creating JWT keys..."
        mkdir -p Secrets
        openssl genpkey -algorithm Ed25519 -out ./Secrets/jwt/jwt_private.pem
        openssl pkey -in ./Secrets/jwt/jwt_private.pem -pubout -out ./Secrets/jwt/jwt_public.pem
        ;;

    --upgrade)
        TARGET="${1:-head}"
        echo "1️⃣  Applying migrations (upgrade head)..."
        docker compose run --rm api_auth sh -c "cd /api && alembic upgrade head"
        ;;

    --targeted)
        TARGET="${1:-head}"
        echo "1️⃣  Upgrading database to target revision: $TARGET"
        docker compose run --rm api_auth sh -c "cd /api && alembic upgrade \"$TARGET\""
        ;;

    --heads)
        echo "1️⃣  Showing current migration heads..."
        docker compose run --rm api_auth sh -c "cd /api && alembic heads"
        ;;

    --rollback)
        TARGET="${1:--1}"
        echo "1️⃣  Rolling back migration (target: $TARGET)..."
        docker compose run --rm api_auth sh -c "cd /api && alembic downgrade \"$TARGET\""
        ;;

    # ===========================================
    #   Database backup and restore
    # ===========================================
    --backup)
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        BACKUP_DIR="./backups"
        mkdir -p "$BACKUP_DIR"

        BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
        echo "Creating database backup: $BACKUP_FILE"

        if docker compose exec -T db pg_dump -U "${DB_USER}" -d "${DB_NAME}" > "$BACKUP_FILE"; then
            echo "✅ Backup completed successfully."
        else
            echo "❌ Backup failed."
            rm -f "$BACKUP_FILE"
        fi
        ;;

    --restore)
        FILE="${1:-}"
        if [ -z "$FILE" ]; then
            echo "Usage: ./launcher.sh --restore <path_to_backup.sql>"
            exit 1
        fi
        echo "Restoring database from $FILE..."
        docker compose exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" < "$FILE"
        echo "✅ Restore completed."
        ;;

    # ===========================================
    # 🆘 Help
    # ===========================================
    --help | -h | "" | *)
        cat <<EOF
Usage: $(basename "$0") [option] [args]

IIP-Visualizador Launcher — manages containers and database migrations

Docker Commands:
    --setup                Initialize the system with generated configuration.
    --start,   -s          Start all services in detached mode.
    --clean,   -c          Stop and remove all containers, networks, and volumes.

Database (Alembic) Commands:
    --schema               Create database schema.
    --generate             Generate the initial migration script.
    --create-keys          Create jwt keys.
    --upgrade              Upgrade the database to the latest version.
    --targeted [rev]       Upgrade DB to target revision.
    --heads                Show current migration heads.
    --rollback [rev]       Downgrade database (default: -1).
    --backup               Create a timestamped database backup.
    --restore [file]       Restore from a .sql backup.

Other:
    --help, -h             Show this help message.

Examples:
    ./launcher.sh --build
    ./launcher.sh --start
    ./launcher.sh --setup
    ./launcher.sh --rollback -1
EOF
        exit 0
        ;;

esac
