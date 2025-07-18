#!/bin/bash

# Simple Database Migration Script
# This script runs the detailed migration script from the project root

set -e

echo "Starting database migration..."
echo ""

# Run the detailed migration script
./nextjs/scripts/migrate.sh

echo ""
echo "Migration script completed!" 