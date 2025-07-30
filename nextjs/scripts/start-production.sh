#!/bin/bash
set -e

echo "🚀 Starting production deployment..."

# Run database migrations
echo "📦 Running database migrations..."
npx prisma migrate deploy

# Generate Prisma client (in case it wasn't generated during build)
echo "🔧 Generating Prisma client..."
npx prisma generate

# Start the Next.js application
echo "✅ Starting Next.js application..."
npm run start