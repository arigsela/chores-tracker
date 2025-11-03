# Type Checking with mypy

This project uses **mypy** for static type checking to catch type errors before runtime.

## Current Status

**Baseline**: 160 type errors (as of Phase 1, Task 1.5 - 2025-11-02)

The mypy infrastructure has been established with a **pragmatic configuration** that:
- ✅ Excludes one-time scripts (`app/scripts/`)
- ✅ Allows gradual typing (not strict mode)
- ✅ Focuses on production code quality
- ✅ Provides a baseline for incremental improvement

## Running mypy

```bash
# From backend directory
cd backend
mypy app/ --config-file mypy.ini

# Or via Docker
docker-compose exec api sh -c "cd /app/backend && mypy app/ --config-file mypy.ini"
```

## Known Issue Categories

### 1. SQLAlchemy 2.0 Compatibility (~40 errors)
- `Sequence` vs `list` return types
- `declared_attr` type mismatches
- Base class typing issues

**Resolution**: Future PRs will add proper type: ignore comments or use cast()

### 2. Multi-Assignment Migration (~20 errors)
- Old code accessing `Chore.is_completed` (moved to `ChoreAssignment`)
- Service layer using deprecated attributes

**Resolution**: Clean up in Phase 3 (Backend Modernization)

### 3. Optional/None Checking (~30 errors)
- Union type attribute access (`Item "None" has no attribute "id"`)
- Operator comparisons with None

**Resolution**: Add proper None guards incrementally

### 4. Pydantic v2 Compatibility (~10 errors)
- `ConfigDict` vs `SettingsConfigDict` mismatch

**Resolution**: Update to Pydantic v2 patterns in Phase 3

### 5. Minor Issues (~60 errors)
- Import type stubs
- Type annotation completeness
- Generic type constraints

## Future Improvements

**Phase 2-3 Goals**:
- Reduce to <100 errors
- Fix all SQLAlchemy typing issues
- Add type: ignore with justifications where needed

**Phase 4-5 Goals**:
- Reduce to <50 errors
- Enable stricter mypy settings incrementally
- Add pre-commit hook for mypy

**Long-term Goals**:
- Zero mypy errors
- Enable `disallow_untyped_defs = True`
- Full strict mode compliance

## Configuration

See `backend/mypy.ini` for current settings.

Key settings:
- `exclude = app/scripts/` - Skip one-time migration scripts
- `no_implicit_optional = False` - Allow Optional[] to be implicit
- `warn_return_any = False` - Don't warn on Any returns (yet)
- `disable_error_code = return-value` for repositories (Sequence vs list)

## Type Stubs

Required type stub packages:
- `types-passlib` - Password hashing
- `types-python-jose` - JWT tokens
