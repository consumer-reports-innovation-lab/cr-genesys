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

# Build the application
RUN npm run build

# Expose port (will be overridden by Render)
EXPOSE 3000

# Start production server with migrations and dynamic port
CMD ["sh", "-c", "NODE_TLS_REJECT_UNAUTHORIZED=0 npx prisma migrate deploy && NODE_TLS_REJECT_UNAUTHORIZED=0 npx prisma generate && npm run start -- -H 0.0.0.0 -p ${PORT:-3000}"]
