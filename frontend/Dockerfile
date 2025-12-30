FROM node:20-slim

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy pnpm workspace files from the frontend subdirectory
COPY frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml frontend/package.json ./

# Copy all packages and apps (source code)
COPY frontend/packages ./packages
COPY frontend/apps ./apps

# Configure pnpm to use the private registry inside Docker
# Docker Desktop for Windows mapping host localhost to host.docker.internal
RUN npm config set @civic:registry http://host.docker.internal:4873

# Install all dependencies
RUN pnpm install


# Expose the main host app port
EXPOSE 3000

# Start the dev server
CMD ["pnpm", "dev"]
