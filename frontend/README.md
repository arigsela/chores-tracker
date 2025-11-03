# Chores Tracker - Frontend

React Native Web frontend for the Chores Tracker application, built with Expo SDK 53.

## Tech Stack

- **Framework**: React Native Web + Expo
- **Language**: TypeScript
- **Navigation**: React Navigation
- **State Management**: Context API
- **API Client**: Axios
- **Testing**: Jest + React Native Testing Library
- **Styling**: React Native StyleSheet

## Development Setup

### Prerequisites

- Node.js 20.x
- npm or yarn

### Local Development

```bash
# Install dependencies
npm install

# Start development server (web)
npm run web

# Run tests
npm test

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build
```

The development server will start on `http://localhost:8081` and connect to the backend API at `http://localhost:8000`.

## Docker Build Process

### Overview

The frontend uses a **two-stage build process**:

1. **Build Stage** (CI/CD or local): Build the web application using Expo
2. **Runtime Stage** (Docker): Serve static files with nginx

### Active Dockerfile: `Dockerfile.working`

The project uses **`Dockerfile.working`** for production deployments. This Dockerfile:

- **Expects pre-built static files** in the `dist/` directory
- Uses nginx:alpine base image
- Injects runtime configuration via `/config.js`
- Runs as non-root user (`nextjs:nodejs`)
- Exposes port 3000

**Why "Dockerfile.working"?**
- The `.working` suffix distinguishes it from the removed full-build Dockerfile
- It's "working" because it expects pre-built files (separation of concerns)
- Used by both `docker-compose.yml` and CI/CD workflows

### Build Process

#### Local Development with Docker Compose

```bash
# Build the frontend static files first
cd frontend
npm run build

# Then start all services (uses Dockerfile.working)
cd ..
docker-compose up frontend
```

The `docker-compose.yml` mounts the local `dist/` directory into the container.

#### CI/CD Production Build

The GitHub Actions workflow (`.github/workflows/frontend-release-and-deploy.yml`) follows this sequence:

1. **Install dependencies**: `npm ci`
2. **Run quality checks**: `npm run lint`, `npm run type-check`, `npm test:ci`
3. **Build application**: `npm run build` (creates `dist/` directory)
4. **Build Docker image**: Uses `Dockerfile.working` with pre-built dist/
5. **Push to ECR**: Pushes image to AWS Elastic Container Registry

### Configuration Management

The frontend supports **runtime configuration** for environment-specific settings:

- **Development**: Uses `public/config.dev.js`
- **Production**: Generates `config.js` at container startup via entrypoint script

Configuration is injected into the HTML at build time:
```html
<script src="/config.js"></script>
```

This allows changing the API URL without rebuilding the Docker image.

### Key Files

- **`Dockerfile.working`**: Production nginx container (expects pre-built dist/)
- **`nginx.conf`**: nginx server configuration (SPA routing, CORS, etc.)
- **`40-generate-config.sh`**: Runtime config generation script
- **`public/config.js`**: Default configuration
- **`public/config.js.template`**: Template for runtime generation
- **`.dockerignore.working`**: Files to exclude from Docker context

### Why Not a Multi-Stage Dockerfile?

**Previous Approach** (removed):
- Single `Dockerfile` with multi-stage build (Node build stage + nginx runtime)
- Built the application **inside Docker** every time

**Current Approach** (Dockerfile.working):
- Build happens **outside Docker** (CI/CD or local `npm run build`)
- Docker only packages pre-built static files
- **Advantages**:
  - Faster Docker builds (no npm install/build inside Docker)
  - Better layer caching in CI/CD
  - Clear separation: npm builds code, Docker packages artifacts
  - Easier debugging (can test build separately from containerization)

## Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test ActivityFeed.test.tsx
```

## Production Deployment

### Manual Build & Push to ECR

```bash
# 1. Build the frontend
cd frontend
npm run build

# 2. Build Docker image
docker build -f Dockerfile.working -t chores-frontend:latest .

# 3. Tag for ECR
docker tag chores-frontend:latest 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-frontend:v1.0.0

# 4. Push to ECR
docker push 852893458518.dkr.ecr.us-east-2.amazonaws.com/chores-frontend:v1.0.0
```

### Automated Deployment

Use the GitHub Actions workflow:

```bash
# Trigger via GitHub UI or gh CLI
gh workflow run frontend-release-and-deploy.yml \
  -f release_type=minor \
  -f release_notes="My release notes"
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client modules
│   ├── components/       # Reusable React components
│   ├── contexts/         # React Context providers
│   ├── navigation/       # React Navigation setup
│   ├── screens/          # Main app screens
│   ├── test-utils/       # Testing utilities and factories
│   └── __tests__/        # Test files
├── public/               # Static files (config, favicon, etc.)
├── dist/                 # Build output (git-ignored)
├── Dockerfile.working    # Production nginx Dockerfile
├── nginx.conf            # nginx configuration
├── package.json          # Dependencies and scripts
└── tsconfig.json         # TypeScript configuration
```

## Environment Variables

The frontend supports these environment variables:

- **`REACT_APP_API_URL`**: Backend API URL (build-time)
- **`NODE_ENV`**: Environment (development/production)

For **runtime configuration** (Docker deployments), use `window.APP_CONFIG` in `config.js`:

```javascript
// public/config.js
window.APP_CONFIG = {
  API_URL: 'https://api.example.com/api/v1',
  NODE_ENV: 'production'
};
```

## Common Issues

### Docker build fails with "dist/ not found"

**Problem**: `Dockerfile.working` expects pre-built static files.

**Solution**: Run `npm run build` before `docker build`.

### Changes not reflected in browser

**Problem**: Browser cache or stale build.

**Solution**:
```bash
# Clear dist/ and rebuild
rm -rf dist/
npm run build

# Or clear browser cache (Cmd+Shift+R on Mac)
```

### nginx fails to start in Docker

**Problem**: Permission issues or port conflicts.

**Solution**:
```bash
# Check if port 3000 is in use
lsof -i :3000

# Check Docker logs
docker-compose logs frontend
```

## Contributing

When making changes to the frontend:

1. Run tests: `npm test`
2. Check types: `npm run type-check`
3. Lint code: `npm run lint`
4. Build successfully: `npm run build`
5. Test Docker build: `docker build -f Dockerfile.working -t test .`

## Links

- [Expo Documentation](https://docs.expo.dev/)
- [React Native Web](https://necolas.github.io/react-native-web/)
- [React Navigation](https://reactnavigation.org/)
- [nginx Documentation](https://nginx.org/en/docs/)
