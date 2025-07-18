# Database Migration Scripts for CR-Genesys

This directory contains scripts to handle database migrations and setup in the Docker environment.

## Scripts Overview

### 1. `setup.sh` - Complete Setup Script
**Purpose**: Handles the entire setup process from Colima to database migration.

**What it does**:
- Checks and starts Colima if needed
- Sets up Docker host configuration
- Starts all Docker containers
- Waits for containers to be ready
- Runs database migration
- Shows application status

**Usage**:
```bash
./setup.sh
```

### 2. `migrate-db.sh` - Database Migration Script
**Purpose**: Runs the detailed migration script from the project root.

**What it does**:
- Calls the detailed migration script in `nextjs/scripts/migrate.sh`

**Usage**:
```bash
./migrate-db.sh
```

### 3. `nextjs/scripts/migrate.sh` - Detailed Migration Script
**Purpose**: Handles all database-related operations in Docker.

**What it does**:
- Checks Docker connection
- Verifies Next.js container is running
- Waits for database to be ready
- Generates Prisma client (with certificate workaround)
- Pushes database schema
- Runs migrations (if any)
- Seeds database (if seed script exists)
- Verifies database setup

**Usage**:
```bash
./nextjs/scripts/migrate.sh
```

### 4. `reset-db.sh` - Database Reset Script
**Purpose**: Resets the database for development purposes.

**What it does**:
- Confirms the reset operation with user
- Drops and recreates the database
- Runs database migration after reset
- Provides fresh database for development

**Usage**:
```bash
./reset-db.sh
```

**Warning**: This will completely remove all data in the database!

## Prerequisites

1. **Colima**: Must be installed and running
   ```bash
   # Install Colima (if not already installed)
   brew install colima
   
   # Start Colima
   colima start
   ```

2. **Docker Compose**: Must be available
   ```bash
   # Install Docker Compose (if not already installed)
   brew install docker-compose
   ```

3. **Scripts**: Must be executable
   ```bash
   chmod +x setup.sh
   chmod +x migrate-db.sh
   chmod +x nextjs/scripts/migrate.sh
   chmod +x reset-db.sh
   ```

## Quick Start

### Option 1: Complete Setup (Recommended)
Run the complete setup script to handle everything:

```bash
./setup.sh
```

### Option 2: Manual Steps
If you prefer to run steps manually:

1. **Start containers**:
   ```bash
   export DOCKER_HOST="unix:///Users/bunyan/.colima/default/docker.sock"
   docker-compose up --build -d
   ```

2. **Run migration**:
   ```bash
   ./migrate-db.sh
   ```

## Troubleshooting

### Certificate Issues
The scripts handle Prisma certificate issues by setting `NODE_TLS_REJECT_UNAUTHORIZED=0` when running Prisma commands.

### Container Not Found
If you get "container not found" errors:
1. Ensure containers are running: `docker-compose ps`
2. Start containers: `docker-compose up -d`

### Database Connection Issues
If database connection fails:
1. Check if PostgreSQL container is running: `docker ps | grep postgres`
2. Wait a few more seconds for database to initialize
3. Check database logs: `docker-compose logs db`

### Permission Issues
If scripts are not executable:
```bash
chmod +x setup.sh
chmod +x migrate-db.sh
chmod +x nextjs/scripts/migrate.sh
```

## Application URLs

After successful setup, your application will be available at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Database**: localhost:5432
- **PgAdmin**: http://localhost:5050

## Database Schema

The migration creates the following tables:
- `users` - User accounts and authentication
- `accounts` - OAuth accounts (NextAuth.js)
- `sessions` - User sessions (NextAuth.js)
- `verification_tokens` - Email verification tokens
- `authenticators` - WebAuthn authenticators
- `chats` - Chat conversations
- `messages` - Chat messages

## Environment Variables

The scripts use the following environment variables (configured in `docker-compose.yml`):

- `DATABASE_URL`: PostgreSQL connection string
- `NEXTAUTH_SECRET`: NextAuth.js secret
- `NEXTAUTH_URL`: NextAuth.js URL
- `INTERNAL_API_URL`: Internal API URL for server-to-server calls
- `NEXT_PUBLIC_API_URL`: Public API URL for client-side calls

## Manual Database Operations

If you need to run database operations manually:

```bash
# Generate Prisma client
docker exec -e NODE_TLS_REJECT_UNAUTHORIZED=0 nextjs_app npx prisma generate

# Push schema changes
docker exec -e NODE_TLS_REJECT_UNAUTHORIZED=0 nextjs_app npx prisma db push

# Run migrations
docker exec -e NODE_TLS_REJECT_UNAUTHORIZED=0 nextjs_app npx prisma migrate deploy

# Seed database
docker exec nextjs_app npm run db:seed

# Open Prisma Studio
docker exec -p 5555:5555 nextjs_app npx prisma studio --hostname 0.0.0.0
```

## Support

If you encounter issues:

1. Check the script output for error messages
2. Verify all prerequisites are met
3. Check container logs: `docker-compose logs`
4. Ensure Colima is running: `colima status` 