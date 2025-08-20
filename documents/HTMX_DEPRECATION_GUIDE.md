# HTMX to React Native Web Migration Guide

## 🚨 DEPRECATION NOTICE

The HTMX/Server-side rendered UI is being deprecated in favor of a modern React Native Web frontend. This document provides guidance for the migration process.

## Migration Timeline

| Phase | Status | Target Date | Description |
|-------|--------|-------------|-------------|
| Phase 1-5 | ✅ COMPLETED | Q1 2025 | API parity & React Native Web development |
| Phase 5.2 | 🔄 IN PROGRESS | Q1 2025 | Adding deprecation notices |
| Phase 6 | 📅 PLANNED | Q2 2025 | CI/CD setup for new frontend |
| Phase 7 | 📅 PLANNED | Q3 2025 | HTMX retirement & cleanup |

## What's Changing?

### Old Stack (Being Deprecated)
- **Frontend**: Server-side rendered HTML with HTMX
- **Templates**: Jinja2 templates in `backend/app/templates/`
- **Routing**: HTML routes in `backend/app/main.py`
- **State**: Server-side sessions
- **Styling**: Inline styles and CSS

### New Stack (Current)
- **Frontend**: React Native Web (Expo)
- **Location**: Separate `frontend/` directory
- **State**: Client-side with AsyncStorage
- **API**: RESTful JSON endpoints only
- **Styling**: React Native StyleSheet

## For Developers

### During Transition Period

Both UIs will remain functional during the transition. However:

1. **New Features**: Implement in React Native Web only
2. **Bug Fixes**: Apply to both if critical, React Native only if minor
3. **API Changes**: Ensure backward compatibility

### API Endpoint Mapping

| HTMX Route | React Native Equivalent | API Endpoint |
|------------|-------------------------|--------------|
| `/` | `LoginScreen` | `POST /api/v1/users/login` |
| `/dashboard` | `DashboardScreen` | `GET /api/v1/users/me` |
| `/chores` | `ChoresScreen` | `GET /api/v1/chores/` |
| `/users` | `ChildrenScreen` | `GET /api/v1/users/my-children` |
| `/reports` | Not implemented | `GET /api/v1/reports/potential-earnings` |

### Component Migration Examples

#### Old (HTMX/Jinja2)
```html
<!-- templates/components/chore_item.html -->
<div class="chore-card" hx-target="this">
  <h3>{{ chore.title }}</h3>
  <p>${{ chore.reward }}</p>
  <button hx-post="/api/v1/chores/{{ chore.id }}/complete">
    Complete
  </button>
</div>
```

#### New (React Native Web)
```tsx
// components/ChoreCard.tsx
<View style={styles.card}>
  <Text style={styles.title}>{chore.title}</Text>
  <Text style={styles.reward}>${chore.reward}</Text>
  <TouchableOpacity onPress={() => completeChore(chore.id)}>
    <Text>Complete</Text>
  </TouchableOpacity>
</View>
```

## For Users

### What to Expect

1. **Parallel Availability**: Both UIs available during transition
2. **Feature Parity**: 90% feature parity already achieved
3. **Performance**: Improved client-side performance
4. **Mobile Ready**: Better mobile experience

### How to Access Each Version

- **Current HTMX UI**: `http://localhost:8000`
- **New React Native Web**: `http://localhost:8081`

### Features Not Yet Migrated

The following features are not yet available in the React Native Web version:

1. **Reports**: Potential earnings report
2. **Admin**: Parent self-registration
3. **Password**: Child password reset (parents)
4. **Bulk Ops**: Bulk assign/approve operations

## Migration Checklist for Teams

### Before Phase 7 (HTMX Retirement)

- [ ] Ensure all users migrated to React Native Web
- [ ] Export any HTMX-specific data if needed
- [ ] Update deployment configurations
- [ ] Update monitoring and logging
- [ ] Update documentation links
- [ ] Train support team on new UI

### Phase 7 Cleanup Tasks

- [ ] Remove `backend/app/templates/` directory
- [ ] Remove HTML routes from `backend/app/main.py`
- [ ] Remove Jinja2 dependency
- [ ] Remove HTMX static files
- [ ] Update nginx/proxy configurations
- [ ] Update CI/CD pipelines

## Code Deprecation Markers

All deprecated code is marked with:

```python
# DEPRECATED: This HTML endpoint will be removed in Phase 7.
# Use the JSON API equivalent: GET /api/v1/...
```

## Testing During Migration

### Parallel Testing Strategy

1. **API Tests**: Continue running all API tests
2. **HTMX Tests**: Keep minimal smoke tests only
3. **React Tests**: Full test coverage required
4. **E2E Tests**: Run against React Native Web

### Test Coverage Requirements

- React Native Web: >80% coverage required
- API endpoints: >90% coverage maintained
- HTMX: Smoke tests only (deprecating)

## Rollback Plan

If issues arise with the React Native Web version:

1. **Immediate**: Users can switch back to HTMX UI
2. **Short-term**: Bug fixes applied to both UIs
3. **Long-term**: Feature freeze on HTMX, fixes to React only

## Support and Resources

### Documentation
- [React Native Web Frontend README](../frontend/README.md)
- [API Documentation](http://localhost:8000/docs)
- [Migration Plan](./FRONTEND_MIGRATION_PLAN.md)

### Getting Help
- GitHub Issues: Report bugs in either UI
- Slack: #frontend-migration channel
- Email: dev-team@chores-tracker.com

## FAQ

**Q: When will the HTMX UI be completely removed?**
A: Target is Q3 2025, but depends on user migration success.

**Q: Will my data be affected?**
A: No, all data is stored in the same backend database.

**Q: Can I use both UIs simultaneously?**
A: Yes, during the transition period both are available.

**Q: What about mobile apps?**
A: The React Native Web code is mobile-ready and can be compiled for iOS/Android.

**Q: Will the API change?**
A: No breaking changes. New endpoints may be added.

## Appendix: Deprecated Endpoints

The following HTML endpoints are deprecated and will be removed:

### Page Routes
- `GET /` → Use React Native Web app
- `GET /dashboard` → Use React Native Web app
- `GET /chores` → Use React Native Web app
- `GET /users` → Use React Native Web app
- `GET /reports` → Use React Native Web app

### Component Routes
- `GET /components/*` → No longer needed
- `GET /pages/*` → No longer needed

### HTML API Routes
- All `/api/v1/html/*` routes → Use JSON equivalents
- Form submission endpoints → Use JSON API

---

**Last Updated**: 2025-08-11
**Status**: Migration in progress (Phase 5.2)
**Contact**: dev-team@chores-tracker.com