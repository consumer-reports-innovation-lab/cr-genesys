#!/bin/bash

# Database Migration Script for Docker
# This script handles Prisma database setup in the Docker environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker connection..."
    
    if ! docker ps > /dev/null 2>&1; then
        print_error "Docker is not accessible. Please ensure Colima is running."
        print_status "You can start Colima with: colima start"
        exit 1
    fi
    
    print_success "Docker is accessible"
}

# Check if Next.js container is running
check_container() {
    print_status "Checking if Next.js container is running..."
    
    if ! docker ps --format "table {{.Names}}" | grep -q "nextjs_app"; then
        print_error "Next.js container (nextjs_app) is not running."
        print_status "Please start the containers with: docker-compose up -d"
        exit 1
    fi
    
    print_success "Next.js container is running"
}

# Wait for database to be ready
wait_for_database() {
    print_status "Waiting for database to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Try to connect to PostgreSQL directly
        if docker exec postgres_db pg_isready -U postgres > /dev/null 2>&1; then
            print_success "Database is ready"
            return 0
        fi
        
        print_status "Database not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_warning "Database readiness check failed, but continuing with migration..."
    print_status "This is normal if the database is still initializing"
}

# Generate Prisma client
generate_prisma_client() {
    print_status "Generating Prisma client..."
    
    if docker exec -e NODE_TLS_REJECT_UNAUTHORIZED=0 nextjs_app npx prisma generate; then
        print_success "Prisma client generated successfully"
    else
        print_error "Failed to generate Prisma client"
        exit 1
    fi
}

# Push database schema
push_schema() {
    print_status "Pushing database schema..."
    
    if docker exec -e NODE_TLS_REJECT_UNAUTHORIZED=0 nextjs_app npx prisma db push; then
        print_success "Database schema pushed successfully"
    else
        print_error "Failed to push database schema"
        exit 1
    fi
}

# Run database migrations (if using migrations instead of db push)
run_migrations() {
    print_status "Running database migrations..."
    
    if docker exec -e NODE_TLS_REJECT_UNAUTHORIZED=0 nextjs_app npx prisma migrate deploy; then
        print_success "Database migrations completed successfully"
    else
        print_warning "No migrations to run or migration failed (this is normal for db push approach)"
    fi
}

# Seed database (if seed script exists)
seed_database() {
    print_status "Checking for database seed script..."
    
    if docker exec nextjs_app test -f "prisma/seed.ts"; then
        print_status "Running database seed..."
        if docker exec nextjs_app npm run db:seed; then
            print_success "Database seeded successfully"
        else
            print_warning "Database seeding failed (this may be normal if no seed data is configured)"
        fi
    else
        print_status "No seed script found, skipping database seeding"
    fi
}

# Verify database setup
verify_setup() {
    print_status "Verifying database setup..."
    
    # Check if users table exists using PostgreSQL directly
    if docker exec postgres_db psql -U postgres -d postgres -c "SELECT COUNT(*) FROM users;" > /dev/null 2>&1; then
        print_success "Database setup verified - users table exists"
    else
        print_warning "Database setup verification failed - users table may not exist yet"
        print_status "This is normal if the schema push is still in progress"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "  Database Migration Script for Docker"
    echo "=========================================="
    echo ""
    
    check_docker
    check_container
    wait_for_database
    generate_prisma_client
    push_schema
    run_migrations
    seed_database
    verify_setup
    
    echo ""
    echo "=========================================="
    print_success "Database migration completed successfully!"
    echo "=========================================="
    echo ""
    print_status "Your application is ready to use:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Database: localhost:5432"
    echo "  - PgAdmin: http://localhost:5050"
    echo ""
}

# Run main function
main "$@" 