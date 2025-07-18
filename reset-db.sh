#!/bin/bash

# Database Reset Script for CR-Genesys
# This script resets the database for development purposes

set -e

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

# Confirm reset
confirm_reset() {
    echo "=========================================="
    echo "  Database Reset Script"
    echo "=========================================="
    echo ""
    print_warning "This will completely reset the database and remove all data!"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Database reset cancelled"
        exit 0
    fi
}

# Reset database
reset_database() {
    print_status "Resetting database..."
    
    # Drop and recreate the database
    docker exec postgres_db psql -U postgres -c "DROP DATABASE IF EXISTS postgres;"
    docker exec postgres_db psql -U postgres -c "CREATE DATABASE postgres;"
    
    print_success "Database reset completed"
}

# Run migration after reset
run_migration() {
    print_status "Running database migration after reset..."
    
    if ./migrate-db.sh; then
        print_success "Database migration completed after reset"
    else
        print_error "Database migration failed after reset"
        exit 1
    fi
}

# Main execution
main() {
    confirm_reset
    reset_database
    run_migration
    
    echo ""
    echo "=========================================="
    print_success "Database reset completed successfully!"
    echo "=========================================="
    echo ""
    print_status "Your application is ready to use with a fresh database:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Database: localhost:5432"
    echo "  - PgAdmin: http://localhost:5050"
    echo ""
}

# Run main function
main "$@" 