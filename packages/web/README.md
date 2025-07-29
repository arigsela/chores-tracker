# Chores Tracker React Frontend

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Page components
├── services/       # API services
├── hooks/          # Custom React hooks
├── contexts/       # React contexts
├── utils/          # Utility functions
├── types/          # TypeScript types
└── styles/         # Global styles
```

## Key Technologies

- React 18 with TypeScript
- Material-UI for components
- React Query for data fetching
- React Hook Form for forms
- Vite for build tooling

## Development Workflow

### Adding a New Page
1. Create page component in `src/pages/`
2. Add route in `src/App.tsx`
3. Update navigation if needed

### Adding a New API Service
1. Define schemas in service file
2. Create service methods
3. Create corresponding hooks
4. Use hooks in components

### Testing
- Unit tests: `npm test`
- E2E tests: `npm run test:e2e`
- Coverage: `npm run test:coverage`

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Docker Development

```bash
# Build development image
docker build -f docker/Dockerfile.dev -t chores-web:dev .

# Run with docker-compose (from project root)
docker-compose up web
```

## Production Build

```bash
# Build production image
docker build -f docker/Dockerfile -t chores-web:prod .

# Run production container
docker run -p 80:80 chores-web:prod
```
