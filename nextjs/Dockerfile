# Production image for Next.js
FROM node:23-alpine
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Generate Prisma client
RUN npx prisma generate

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start production server with migrations
CMD ["sh", "-c", "npx prisma migrate deploy && npx prisma generate && npm run start"]
