# Product Requirements Document: HTMX to React Migration

**Document Version:** 1.0  
**Date:** January 28, 2025  
**Author:** Frontend Stack Advisor

## 1. Executive Summary

The Chores Tracker application currently uses a mixed architecture with FastAPI serving both JSON APIs and HTMX-powered HTML responses. This PRD proposes migrating to a separated backend/frontend architecture with React as the frontend framework, creating a unified technology stack across web and mobile platforms.

### Key Recommendations
- **Frontend Framework:** React 18+ with TypeScript
- **State Management:** React Context API (initially) with potential Redux Toolkit migration
- **UI Library:** Material-UI (MUI) for rapid development with consistent design
- **Build Tool:** Vite for fast development experience
- **API Client:** Axios with React Query for data fetching and caching

This migration will enable code sharing with the existing React Native mobile app, improve developer productivity, and provide a modern user experience while maintaining the simplicity that makes the current solution effective.

## 2. Current State Analysis

### 2.1 Architecture Overview
```
┌─────────────────────────────────────┐
│         Current Architecture        │
├─────────────────────────────────────┤
│  Frontend: HTMX + Jinja2 Templates  │
│  - Server-side rendering            │
│  - Inline JavaScript for auth       │
│  - Mixed JSON/HTML responses        │
├─────────────────────────────────────┤
│    Backend: FastAPI (Python 3.11)   │
│  - Dual API approach                │
│  - JWT authentication               │
│  - Service layer architecture       │
├─────────────────────────────────────┤
│     Database: MySQL 5.7             │
│  - SQLAlchemy 2.0 ORM              │
│  - Async support                    │
├─────────────────────────────────────┤
│   Mobile: React Native (Separate)   │
│  - Uses JSON APIs only              │
│  - Duplicated business logic        │
└─────────────────────────────────────┘
```

### 2.2 Current Implementation Details

**Backend Endpoints:**
- RESTful JSON APIs: `/api/v1/users/`, `/api/v1/chores/`
- HTML Component APIs: `/api/v1/html/` (HTMX-specific)
- Mixed content type handling based on request headers

**Frontend Components:**
- 30+ HTML templates with HTMX attributes
- Inline JavaScript for authentication (localStorage)
- TailwindCSS for styling
- Progressive enhancement with vanilla JavaScript

**Authentication Flow:**
- JWT tokens stored in localStorage
- Manual header injection for HTMX requests
- Role-based UI rendering (parent vs child views)

### 2.3 Pain Points

1. **Code Duplication:** Business logic exists in both web templates and mobile app
2. **Testing Complexity:** HTML responses harder to test than JSON APIs
3. **Limited Interactivity:** HTMX constraints limit complex UI interactions
4. **Mobile/Web Divergence:** Different codebases for similar features
5. **Developer Experience:** Mixed paradigms (server-side + client-side) create cognitive overhead

### 2.4 Strengths to Preserve

1. **Simple Architecture:** Easy to understand data flow
2. **Fast Initial Load:** Server-side rendering provides quick first paint
3. **Progressive Enhancement:** Works without JavaScript (mostly)
4. **Low Complexity:** No build tools or complex state management

## 3. Proposed Architecture

### 3.1 Target Architecture
```
┌─────────────────────────────────────┐
│      Proposed Architecture          │
├─────────────────────────────────────┤
│    Frontend: React SPA              │
│  - TypeScript for type safety       │
│  - Material-UI components           │
│  - React Query for data fetching    │
│  - Shared components with mobile    │
├─────────────────────────────────────┤
│    Backend: FastAPI (JSON only)     │
│  - Pure REST API                    │
│  - Remove HTML endpoints            │
│  - OpenAPI documentation            │
│  - CORS enabled                     │
├─────────────────────────────────────┤
│     Shared Code Repository          │
│  - Common types/interfaces          │
│  - Validation schemas               │
│  - Business logic utilities        │
├─────────────────────────────────────┤
│   Infrastructure Changes            │
│  - CDN for static assets            │
│  - Separate deployments             │
│  - API versioning strategy          │
└─────────────────────────────────────┘
```

### 3.2 Technology Stack Details

**Frontend Stack:**
```javascript
{
  "framework": "React 18.2+",
  "language": "TypeScript 5.0+",
  "buildTool": "Vite 5.0+",
  "stateManagement": "React Context API → Redux Toolkit",
  "uiLibrary": "Material-UI (MUI) 5.0+",
  "dataFetching": "React Query 5.0+ with Axios",
  "routing": "React Router 6.0+",
  "formHandling": "React Hook Form + Zod",
  "testing": "Vitest + React Testing Library",
  "linting": "ESLint + Prettier",
  "deployment": "Docker → AWS S3 + CloudFront"
}
```

**Backend Modifications:**
- Remove all HTML endpoint handlers
- Enhance CORS configuration
- Add API versioning headers
- Implement rate limiting for SPA patterns
- Add WebSocket support for real-time updates

### 3.3 Shared Code Strategy

Create a monorepo structure to share code between web and mobile:

```
chores-tracker/
├── packages/
│   ├── shared/          # Shared types and utilities
│   │   ├── types/       # TypeScript interfaces
│   │   ├── schemas/     # Validation schemas
│   │   └── utils/       # Business logic
│   ├── web/            # React web app
│   └── mobile/         # React Native app
├── backend/            # FastAPI backend
└── infrastructure/     # Deployment configs
```

## 4. Technology Recommendations

### 4.1 Why React?

**Pros for DevOps Engineers:**
1. **Gentle Learning Curve:** Component-based architecture is intuitive
2. **Excellent Documentation:** Official docs + massive community resources
3. **Code Sharing:** Reuse patterns from existing React Native app
4. **Tooling Maturity:** Extensive DevOps-friendly tooling
5. **TypeScript Support:** Catch errors at compile time

**Comparison with Alternatives:**

| Framework | Learning Curve | Code Sharing | Community | DevOps Tools |
|-----------|---------------|--------------|-----------|--------------|
| React | Moderate | Excellent (RN exists) | Massive | Excellent |
| Vue | Easy | Limited | Large | Good |
| Angular | Steep | Limited | Large | Excellent |
| Svelte | Easy | None | Growing | Limited |
| HTMX++ | Minimal | None | Small | Limited |

### 4.2 Material-UI Selection Rationale

1. **Pre-built Components:** Accelerates development without design expertise
2. **Consistent Design:** Professional look out-of-the-box
3. **Accessibility:** WCAG compliant components
4. **Customization:** Theming system for brand consistency
5. **Mobile-Friendly:** Responsive by default

### 4.3 Development Experience Optimizations

**For DevOps Background:**
- Docker-first development environment
- Makefile for common tasks
- Pre-configured CI/CD pipelines
- Automated testing setup
- Infrastructure as Code templates

## 5. Benefits & Trade-offs

### 5.1 Benefits

**Technical Benefits:**
1. **Unified Codebase:** Share 40-60% of code between web and mobile
2. **Better Testing:** Component testing, E2E testing, visual regression
3. **Performance:** Client-side routing, lazy loading, code splitting
4. **Developer Velocity:** Hot module replacement, better debugging
5. **Type Safety:** TypeScript catches errors early

**Business Benefits:**
1. **Feature Parity:** Easier to maintain consistency across platforms
2. **Faster Development:** Reuse components and logic
3. **Better UX:** Richer interactions, real-time updates
4. **Scalability:** Easier to add complex features
5. **Hiring:** Larger React developer pool

### 5.2 Trade-offs

**Complexity Increase:**
- Build process required
- State management complexity
- More moving parts
- Separate deployment pipelines

**Performance Considerations:**
- Larger initial bundle size
- JavaScript required for functionality
- SEO considerations (can be mitigated with SSR)

**Migration Effort:**
- 3-4 month timeline
- Learning curve for team
- Temporary feature freeze
- Parallel maintenance burden

## 6. Success Metrics

### 6.1 Technical Metrics

| Metric | Current (HTMX) | Target (React) | Measurement |
|--------|----------------|----------------|-------------|
| First Contentful Paint | <500ms | <800ms | Lighthouse |
| Time to Interactive | <1s | <2s | Lighthouse |
| Bundle Size | N/A | <200KB (gzipped) | Webpack Analyzer |
| Code Coverage | 43% | >80% | Jest/Vitest |
| Build Time | N/A | <30s | CI/CD logs |
| Deploy Time | 5 min | <3 min | CI/CD logs |

### 6.2 Developer Productivity Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Feature Development Time | -30% | JIRA velocity |
| Bug Fix Time | -40% | Issue tracking |
| Code Reuse | 40-60% | Code analysis |
| PR Review Time | -25% | GitHub metrics |
| Onboarding Time | <1 week | Time to first PR |

### 6.3 User Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User Satisfaction | +20% | NPS surveys |
| Task Completion Rate | +15% | Analytics |
| Error Rate | -50% | Sentry |
| Mobile/Web Feature Parity | 95% | Feature audit |

## 7. Risks & Mitigation

### 7.1 Technical Risks

**Risk 1: Performance Regression**
- **Mitigation:** Implement performance budget, use code splitting, lazy loading
- **Monitoring:** Set up performance monitoring from day 1

**Risk 2: SEO Impact**
- **Mitigation:** Consider Next.js for SSR if SEO critical
- **Alternative:** Implement prerendering for public pages

**Risk 3: Bundle Size Growth**
- **Mitigation:** Tree shaking, dynamic imports, bundle analysis
- **Budget:** Max 200KB gzipped for initial load

### 7.2 Team Risks

**Risk 1: Learning Curve**
- **Mitigation:** 
  - Start with React fundamentals course (2 weeks)
  - Pair programming with React experienced developers
  - Create internal component library with examples
  - Document patterns and best practices

**Risk 2: Maintaining Two Systems**
- **Mitigation:**
  - Feature freeze on HTMX version
  - Incremental migration approach
  - Clear cutover plan

### 7.3 Business Risks

**Risk 1: Extended Timeline**
- **Mitigation:** MVP approach, migrate core features first
- **Contingency:** Ability to extend HTMX if needed

**Risk 2: User Disruption**
- **Mitigation:** 
  - Beta testing program
  - Gradual rollout
  - Feature flags for rollback

## 8. High-level Timeline

### Phase 1: Foundation (Weeks 1-4)
- Set up React project with TypeScript
- Configure build pipeline and CI/CD
- Implement authentication flow
- Create basic layout and routing
- Set up shared code repository

### Phase 2: Core Features (Weeks 5-8)
- Migrate chore management (CRUD)
- Implement child/parent dashboards
- Add real-time updates with WebSockets
- Create component library

### Phase 3: Advanced Features (Weeks 9-12)
- Reward approval workflow
- Reporting and analytics
- Performance optimizations
- Mobile/web code sharing

### Phase 4: Testing & Migration (Weeks 13-16)
- Comprehensive testing
- User acceptance testing
- Migration tools for data
- Gradual rollout plan
- Documentation and training

### Milestones
- **Week 4:** Basic React app with auth working
- **Week 8:** Feature parity for core workflows
- **Week 12:** Full feature parity + improvements
- **Week 16:** Production ready, 20% users migrated

## 9. Implementation Recommendations

### 9.1 Getting Started (Week 1)

```bash
# 1. Create React app with Vite
npm create vite@latest chores-web -- --template react-ts

# 2. Install core dependencies
npm install @mui/material @emotion/react @emotion/styled
npm install @tanstack/react-query axios
npm install react-router-dom
npm install react-hook-form zod @hookform/resolvers

# 3. Set up folder structure
mkdir -p src/{components,pages,services,hooks,types,utils}
```

### 9.2 First Component Example

Transform the HTMX chore list to React:

```typescript
// src/components/ChoreList.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, Typography, Chip } from '@mui/material';
import { choreService } from '../services/choreService';
import { Chore } from '@shared/types';

export const ChoreList: React.FC = () => {
  const { data: chores, isLoading, error } = useQuery({
    queryKey: ['chores'],
    queryFn: choreService.getActiveChores,
  });

  if (isLoading) return <div>Loading chores...</div>;
  if (error) return <div>Error loading chores</div>;

  return (
    <div className="chore-list">
      {chores?.map((chore: Chore) => (
        <Card key={chore.id} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6">{chore.title}</Typography>
            <Typography color="text.secondary">
              {chore.description}
            </Typography>
            <Chip 
              label={`$${chore.reward}`} 
              color="success" 
              size="small" 
            />
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
```

### 9.3 DevOps-Friendly Setup

```dockerfile
# Dockerfile for React app
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

## 10. Conclusion

Migrating from HTMX to React represents a significant architectural shift that will:
1. Unify the technology stack across web and mobile
2. Enable code sharing and faster feature development
3. Provide a foundation for future growth and complexity
4. Improve developer experience and productivity

While the migration involves substantial effort and risk, the long-term benefits of a unified, modern architecture outweigh the short-term costs. The recommended phased approach minimizes risk while delivering value incrementally.

### Next Steps
1. Review and approve this PRD
2. Allocate resources (2-3 developers for 16 weeks)
3. Set up development environment
4. Begin Phase 1 implementation
5. Establish success metrics tracking

### Decision Points
- **Week 2:** Confirm React vs alternatives based on POC
- **Week 4:** Assess progress and adjust timeline
- **Week 8:** Go/no-go for full migration
- **Week 12:** Plan production rollout strategy