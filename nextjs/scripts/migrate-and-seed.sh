#!/bin/bash

# Navigate to the correct directory
cd /app

# Run database migrations
echo "Running database migrations..."
npx prisma migrate deploy

# Generate Prisma client (if not already done)
echo "Generating Prisma client..."
npx prisma generate

# Optionally seed the database (uncomment if you want to seed)
# echo "Seeding database..."
# npm run db:seed

echo "Database setup complete!"