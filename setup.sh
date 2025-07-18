#!/bin/bash

# Complete Setup Script for CR-Genesys
# This script handles the entire setup process from Docker to database migration

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

# Check if Colima is running
check_colima() {
    print_status "Checking Colima status..."
    
    if ! colima status > /dev/null 2>&1; then
        print_warning "Colima is not running. Starting Colima..."
        colima start
        print_success "Colima started successfully"
    else
        print_success "Colima is already running"
    fi
}

# Set Docker host
setup_docker_host() {
    print_status "Setting up Docker host..."
    export DOCKER_HOST="unix:///Users/bunyan/.colima/default/docker.sock"
    print_success "Docker host configured"
}

# Start Docker containers
start_containers() {
    print_status "Starting Docker containers..."
    
    if docker-compose up --build -d; then
        print_success "Docker containers started successfully"
    else
        print_error "Failed to start Docker containers"
        exit 1
    fi
}

# Wait for containers to be ready
wait_for_containers() {
    print_status "Waiting for containers to be ready..."
    sleep 10
    print_success "Containers should be ready"
}

# Run database migration
run_migration() {
    print_status "Running database migration..."
    
    if ./migrate-db.sh; then
        print_success "Database migration completed"
    else
        print_error "Database migration failed"
        exit 1
    fi
}

# Show application status
show_status() {
    print_status "Checking application status..."
    
    echo ""
    echo "=========================================="
    echo "  Application Status"
    echo "=========================================="
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_success "All containers are running"
    else
        print_error "Some containers are not running"
    fi
    
    # Check if services are accessible
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is accessible at http://localhost:3000"
    else
        print_warning "Frontend may not be ready yet"
    fi
    
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        print_success "Backend API is accessible at http://localhost:8000"
    else
        print_warning "Backend API may not be ready yet"
    fi
    
    echo ""
    print_status "Application URLs:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Database: localhost:5432"
    echo "  - PgAdmin: http://localhost:5050"
    echo ""
}

# Main execution
main() {
    echo "=========================================="
    echo "  CR-Genesys Complete Setup Script"
    echo "=========================================="
    echo ""
    
    check_colima
    setup_docker_host
    start_containers
    wait_for_containers
    run_migration
    show_status
    
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    echo ""
    print_status "You can now access your application at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Signup page: http://localhost:3000/signup"
    echo "  - Login page: http://localhost:3000/login"
    echo ""
}

# Run main function
main "$@" 