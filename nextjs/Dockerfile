# Production image for Next.js
FROM node:23-alpine
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Generate Prisma client (disable SSL verification for certificate issues)
RUN NODE_TLS_REJECT_UNAUTHORIZED=0 npx prisma generate

# Skip build for development mode (temporary for debugging)

# Expose port (will be overridden by Render)
EXPOSE 3000

# Start development server with migrations and dynamic port (temporary for debugging)
CMD ["sh", "-c", "NODE_TLS_REJECT_UNAUTHORIZED=0 npx prisma migrate deploy && NODE_TLS_REJECT_UNAUTHORIZED=0 npx prisma generate && npm run dev -- -p ${PORT:-3000}"]
