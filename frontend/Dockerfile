FROM node:20-slim

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy pnpm workspace files from the frontend subdirectory
COPY frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml frontend/package.json ./

# Copy all packages and apps (source code)
# Copy all packages and apps (source code)
COPY frontend/packages ./packages
COPY frontend/vendor ./vendor
COPY frontend/apps ./apps

# Patch pnpm-workspace.yaml to use vendored package instead of external link
# Replaces "../../civic/packages/design-system" with "./vendor/design-system"
RUN sed -i 's|\.\./\.\./civic/packages/design-system|./vendor/design-system|g' pnpm-workspace.yaml

# Install all dependencies
RUN pnpm install

# Expose the main host app port
EXPOSE 3000

# Start the dev server
CMD ["pnpm", "dev"]
