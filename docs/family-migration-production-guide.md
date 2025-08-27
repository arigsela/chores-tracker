# Family Migration Production Deployment Guide

This guide provides step-by-step procedures for safely deploying the multi-parent family feature to production.

## Pre-Deployment Checklist

### Prerequisites
- [ ] Database backup completed and verified
- [ ] Maintenance window scheduled (estimated 15-30 minutes)
- [ ] All stakeholders notified
- [ ] Rollback plan reviewed and approved
- [ ] Migration scripts tested in staging environment

### Environment Validation
```bash
# Verify current migration state
docker-compose exec api python -m alembic -c backend/alembic.ini current

# Run validation script
docker-compose exec api python -m backend.app.scripts.validate_family_migration

# Test edge cases
docker-compose exec api python -m backend.app.scripts.test_migration_edge_cases
```

## Deployment Procedure

### Phase 1: Pre-Migration Safety Checks

#### 1. Create Full Database Backup
```bash
# Stop application services
docker-compose stop api

# Create timestamped backup
BACKUP_FILE="chores_tracker_backup_$(date +%Y%m%d_%H%M%S).sql"
docker-compose exec mysql mysqldump -u root -ppassword123 --single-transaction chores_tracker > $BACKUP_FILE

# Verify backup file
ls -lh $BACKUP_FILE
head -20 $BACKUP_FILE
```

#### 2. Validate Current System State
```bash
# Check system health
docker-compose exec mysql mysql -u root -ppassword123 -e "SELECT 'Database OK' as status;" chores_tracker

# Check current data counts
docker-compose exec mysql mysql -u root -ppassword123 -e "
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE is_parent = 1) as total_parents,
    (SELECT COUNT(*) FROM chores) as total_chores,
    (SELECT COUNT(*) FROM reward_adjustments) as total_adjustments;" chores_tracker
```

#### 3. Enable Maintenance Mode
```bash
# Create maintenance indicator file
touch /tmp/maintenance_mode

# Restart services with maintenance check
docker-compose up -d
```

### Phase 2: Execute Migration

#### 1. Apply Database Migration
```bash
# Apply family migration
docker-compose exec api python -m alembic -c backend/alembic.ini upgrade head

# Expected output should show:
# - Migration validation: Total users: X, Users with family: X, Orphaned users: 0
# - INFO [alembic.runtime.migration] Running upgrade ... -> ..., Add families table and family_id to users
```

#### 2. Immediate Post-Migration Validation
```bash
# Run comprehensive validation
docker-compose exec api python -m backend.app.scripts.validate_family_migration

# Expected: "✅ ALL VALIDATION CHECKS PASSED!"
```

### Phase 3: System Verification

#### 1. Test Core Functionality
```bash
# Test API health
curl -f http://localhost:8000/health

# Test user authentication (replace with actual credentials)
curl -X POST http://localhost:8000/api/v1/users/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass"

# Test user profile access
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me
```

#### 2. Validate Data Integrity
```bash
# Check that all users have families
docker-compose exec mysql mysql -u root -ppassword123 -e "
SELECT COUNT(*) as orphaned_users FROM users WHERE family_id IS NULL;" chores_tracker

# Should return: orphaned_users = 0

# Check family structure
docker-compose exec mysql mysql -u root -ppassword123 -e "
SELECT 
    f.name,
    COUNT(u.id) as members,
    SUM(CASE WHEN u.is_parent = 1 THEN 1 ELSE 0 END) as parents
FROM families f
LEFT JOIN users u ON u.family_id = f.id
GROUP BY f.id, f.name
ORDER BY members DESC
LIMIT 10;" chores_tracker
```

#### 3. Performance Validation
```bash
# Run performance tests
docker-compose exec api python -c "
import asyncio
from backend.app.scripts.test_migration_edge_cases import EdgeCaseTestSuite
from backend.app.db.base import get_db

async def test_perf():
    async for db in get_db():
        suite = EdgeCaseTestSuite(db)
        await suite.test_query_performance()
        break

asyncio.run(test_perf())
"
```

### Phase 4: Application Restart

#### 1. Graceful Application Restart
```bash
# Remove maintenance mode
rm -f /tmp/maintenance_mode

# Restart application services
docker-compose restart api

# Wait for services to be healthy
sleep 30

# Verify health
curl -f http://localhost:8000/health
```

#### 2. Monitor Application Logs
```bash
# Monitor for errors
docker-compose logs -f --tail=50 api

# Check for any unusual activity
docker-compose logs --since=5m api | grep -i error
```

## Post-Deployment Monitoring

### Immediate Monitoring (First 2 Hours)

#### System Health Checks
```bash
# Every 15 minutes for first 2 hours
while true; do
  echo "$(date): Health check"
  curl -s http://localhost:8000/health | jq .
  
  # Check error rates
  docker-compose logs --since=15m api | grep -c ERROR || echo "No errors"
  
  sleep 900  # 15 minutes
done
```

#### Key Metrics to Monitor
- API response times (should be <200ms for family endpoints)
- Database connection pool usage
- Memory usage patterns
- Error rates in application logs

### Extended Monitoring (First Week)

#### Daily Health Checks
```bash
# Run daily validation
docker-compose exec api python -m backend.app.scripts.validate_family_migration

# Check database performance
docker-compose exec mysql mysql -u root -ppassword123 -e "SHOW PROCESSLIST;" chores_tracker
```

#### User Experience Monitoring
- Monitor support ticket volume for family-related issues
- Track user engagement with family features
- Validate invite code generation and usage patterns

## Rollback Procedures

### Emergency Rollback (Critical Issues)

#### 1. Immediate Response
```bash
# Stop application immediately
docker-compose stop api

# Assess the situation
docker-compose logs --since=1h api > /tmp/migration_error_logs.txt
```

#### 2. Execute Emergency Rollback
```bash
# Run emergency rollback script
docker-compose exec api python -m backend.app.scripts.emergency_family_rollback --confirm

# This will:
# - Create backup of current family data
# - Remove family_id column from users
# - Drop families table  
# - Restore original database schema
```

#### 3. Restore from Backup (If Needed)
```bash
# If rollback script fails, restore from backup
docker-compose stop mysql
docker volume rm chores-tracker_mysql_data

# Restore backup
docker-compose up -d mysql
sleep 30
cat $BACKUP_FILE | docker-compose exec -T mysql mysql -u root -ppassword123 chores_tracker

# Restart services
docker-compose up -d
```

### Planned Rollback (Non-Critical Issues)

#### 1. Schedule Maintenance Window
- Notify users of planned rollback
- Document reasons for rollback
- Plan re-deployment timeline

#### 2. Execute Controlled Rollback
```bash
# Use Alembic to rollback to previous migration
docker-compose exec api python -m alembic -c backend/alembic.ini downgrade -1

# Validate rollback
docker-compose exec mysql mysql -u root -ppassword123 -e "SHOW TABLES;" chores_tracker
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Migration Timeout
**Symptoms:** Migration hangs or times out
**Solution:**
```bash
# Check for blocking transactions
docker-compose exec mysql mysql -u root -ppassword123 -e "SHOW PROCESSLIST;" chores_tracker

# Kill blocking processes if necessary
# Then retry migration
```

#### Issue: Circular Parent References
**Symptoms:** Migration validation finds circular references
**Solution:**
```bash
# Find circular references
docker-compose exec mysql mysql -u root -ppassword123 -e "
WITH RECURSIVE parent_chain AS (
  SELECT id, username, parent_id, 0 as depth
  FROM users
  WHERE parent_id IS NOT NULL
  
  UNION ALL
  
  SELECT u.id, u.username, u.parent_id, pc.depth + 1
  FROM users u
  JOIN parent_chain pc ON u.parent_id = pc.id
  WHERE pc.depth < 10
)
SELECT * FROM parent_chain WHERE depth > 5;" chores_tracker

# Manually fix data and re-run migration
```

#### Issue: Performance Degradation
**Symptoms:** Slow API responses after migration
**Solution:**
```bash
# Check for missing indexes
docker-compose exec mysql mysql -u root -ppassword123 -e "
SHOW INDEX FROM users WHERE Key_name LIKE '%family%';" chores_tracker

# Add missing indexes if needed
docker-compose exec mysql mysql -u root -ppassword123 -e "
CREATE INDEX idx_users_family_id ON users(family_id);" chores_tracker
```

### Emergency Contacts

#### Development Team
- Primary: [Lead Developer Contact]
- Secondary: [Backend Developer Contact]
- Database: [DBA Contact]

#### Operations Team
- On-call: [Operations Contact]
- Manager: [Ops Manager Contact]

### Support Escalation

#### Level 1: Application Restart
- Restart services
- Check basic connectivity
- Monitor for immediate errors

#### Level 2: Database Issues
- Check database connectivity
- Validate data integrity
- Consider rollback if critical

#### Level 3: Full Rollback
- Execute emergency rollback procedures
- Restore from backup if necessary
- Full post-mortem analysis

## Success Criteria

### Technical Success Metrics
- ✅ Zero data loss during migration
- ✅ All validation scripts pass
- ✅ API response times <200ms
- ✅ No increase in error rates
- ✅ All existing functionality preserved

### Business Success Metrics
- ✅ <5% increase in support tickets
- ✅ Multi-parent feature adoption >10% within first week
- ✅ No user complaints about data loss
- ✅ Successful invite code generation and usage

### Rollback Triggers
- Data integrity violations discovered
- API response times >500ms consistently
- Error rates >1% for core operations
- Critical functionality broken
- User data corruption detected

---

**Document Version:** 1.0  
**Last Updated:** 2025-08-26  
**Review Schedule:** Post-deployment + 1 week, then quarterly  
**Approval Required:** Lead Developer, DevOps Manager, Product Owner