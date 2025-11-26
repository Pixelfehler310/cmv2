# Open RPG Engine - Frontend

This is the frontend monorepo for the Open RPG Engine, built with React, Vite, and pnpm workspaces using a Microfrontends (MFE) architecture.

## Prerequisites

- Node.js >= 18.0.0
- pnpm >= 8.0.0

## Getting Started

### 1. Install Dependencies

From the `frontend` directory, run:

```bash
pnpm install
```

This will install all dependencies for the workspace, including:
- App Shell (`apps/host`)
- Player Sheet MFE (`apps/player-sheet`)
- DM Tools MFE (`apps/dm-tools`)
- Cartographer MFE (`apps/cartographer`)
- Shared packages (`packages/types`, `packages/ui`)

### 2. Start Development Server

To run all MFEs in parallel:

```bash
pnpm dev
```

This will start:
- App Shell (Host) on `http://localhost:5173`
- Player Sheet MFE on `http://localhost:5174`
- DM Tools MFE on `http://localhost:5175`
- Cartographer MFE on `http://localhost:5176`

### 3. Environment Variables

Create a `.env` file in the `apps/host` directory (or use environment variables):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Project Structure

```
frontend/
├── apps/
│   ├── host/              # App Shell (main application)
│   ├── player-sheet/      # Player Sheet MFE
│   ├── dm-tools/          # DM Tools MFE
│   └── cartographer/      # Map/Cartographer MFE
├── packages/
│   ├── types/             # Shared TypeScript types
│   └── ui/                # Shared UI components
└── package.json           # Root workspace configuration
```

## Available Scripts

### Root Level

- `pnpm dev` - Start all MFEs in parallel
- `pnpm build` - Build all packages
- `pnpm test` - Run tests in all packages
- `pnpm lint` - Lint all packages

### Individual Packages

Each package has its own scripts. Navigate to the package directory and run:

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm test` - Run tests
- `pnpm lint` - Lint code

## Architecture

### Microfrontends (MFE)

The frontend is organized as microfrontends:

1. **App Shell (Host)**: 
   - Main application container
   - Manages routing, authentication, WebSocket connection
   - Provides event bus and action dispatcher
   - Uses FlexLayout for docking windows

2. **Player Sheet MFE**:
   - Character display and management
   - Stats, inventory, spells, features tabs

3. **DM Tools MFE**:
   - Monster library
   - Campaign management
   - Initiative tracker
   - Item/Spell browsers
   - Creation forms

4. **Cartographer MFE**:
   - Map display with PixiJS
   - Grid system
   - Token management

### Shared Packages

- **@rpg/types**: TypeScript interfaces matching backend Pydantic models
- **@rpg/ui**: Reusable UI components (shadcn/ui based)

## Development

### Adding a New MFE

1. Create a new directory in `apps/`
2. Add package.json with workspace dependencies
3. Configure Vite with appropriate port
4. Add to `pnpm-workspace.yaml` (already includes `apps/*`)
5. Integrate into App Shell's Workbench layout

### Adding Shared Components

Add components to `packages/ui/src/components/` and export from `packages/ui/index.ts`

## Testing

Tests are set up with Vitest and React Testing Library. Run tests with:

```bash
pnpm test
```

## Building for Production

```bash
pnpm build
```

This will build all packages. The App Shell will be the main entry point.

## Troubleshooting

### Port Already in Use

If a port is already in use, you can:
1. Change the port in the MFE's `vite.config.ts`
2. Kill the process using the port

### Workspace Dependencies Not Found

Run `pnpm install` from the root `frontend` directory to ensure all workspace dependencies are linked.

### TypeScript Errors

Make sure all packages are built:
```bash
pnpm build
```

Or run TypeScript in watch mode in each package.

