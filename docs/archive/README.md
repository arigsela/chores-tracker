# Documentation Archive

This directory contains historical documentation that has been archived for reference purposes. These documents are no longer actively maintained but are preserved for historical context, audit trails, and lessons learned.

## Table of Contents

- [Why Archive?](#why-archive)
- [Archive Categories](#archive-categories)
  - [Migration Documentation](#migration-documentation)
  - [Assessment Reports](#assessment-reports)
  - [Project Phase Reports](#project-phase-reports)
  - [Deprecated Features](#deprecated-features)
  - [Historical Decisions](#historical-decisions)
- [Archived Documents](#archived-documents)
- [How to Use This Archive](#how-to-use-this-archive)
- [Archival Process](#archival-process)

## Why Archive?

Documentation is archived when it:
- Describes features or systems that have been replaced or removed
- Contains project assessments or audits that are complete
- Documents migration processes that are finished
- Represents historical decision-making context
- Is no longer relevant to current operations but valuable for reference

**We archive rather than delete because:**
- Historical context helps understand current architecture
- Audit trails are important for compliance and learning
- Past decisions inform future choices
- Onboarding benefits from understanding project evolution

## Archive Categories

### Migration Documentation

Documentation related to major system migrations that are now complete.

**Examples:**
- HTMX to React Native Web migration
- SQLAlchemy 1.x to 2.0 upgrade
- Database engine changes
- Kubernetes cluster migrations

### Assessment Reports

One-time reports, audits, and quality assessments.

**Examples:**
- Security audit reports (post-remediation)
- Documentation quality assessments
- Code review reports
- DevOps maturity scorecards

### Project Phase Reports

Reports documenting specific project phases or sprints that are complete.

**Examples:**
- Phase completion summaries
- Sprint retrospectives
- Proof-of-concept results
- Feasibility studies

### Deprecated Features

Documentation for features that have been removed or replaced.

**Examples:**
- Legacy API endpoints
- Deprecated authentication methods
- Removed frontend components
- Retired deployment methods

### Historical Decisions

Architecture Decision Records (ADRs) and design documents for decisions that have been superseded.

**Examples:**
- Technology selection rationale (when technology changed)
- Initial architecture designs (before refactoring)
- Performance optimization experiments
- A/B test results

## Archived Documents

### Active Candidates for Archival

The following documents in the `/docs` root are candidates for archival based on their nature:

#### Assessment and Review Reports

**CI_CD_PIPELINE_REVIEW.md**
- **Type**: Assessment Report
- **Date**: Unknown
- **Reason for Archive**: One-time review, likely complete
- **Value**: Historical reference for CI/CD evolution
- **Status**: Candidate for archival

**COMPREHENSIVE_REVIEW_FINAL_REPORT.md**
- **Type**: Assessment Report
- **Date**: Unknown
- **Reason for Archive**: Final report implies completion
- **Value**: Comprehensive system snapshot at a point in time
- **Status**: Candidate for archival

**DEVOPS_SCORECARD.md**
- **Type**: Assessment Report
- **Date**: Unknown
- **Reason for Archive**: Point-in-time maturity assessment
- **Value**: Benchmark for DevOps improvement over time
- **Status**: Candidate for archival

**DOCUMENTATION_QUALITY_ASSESSMENT.md**
- **Type**: Assessment Report
- **Date**: Unknown
- **Reason for Archive**: One-time quality assessment
- **Value**: Historical documentation quality metrics
- **Status**: Candidate for archival

**DOCUMENTATION_VERIFICATION_REPORT.md**
- **Type**: Assessment Report
- **Date**: Unknown
- **Reason for Archive**: Verification completed
- **Value**: Reference for documentation standards
- **Status**: Candidate for archival

**SECURITY_AUDIT_REPORT.md**
- **Type**: Security Audit
- **Date**: Unknown
- **Reason for Archive**: Audit findings addressed
- **Value**: Security posture evolution, compliance records
- **Status**: Candidate for archival (after remediation complete)

#### Project Phase Documentation

**PHASE_4B_FINAL_REPORT.md**
- **Type**: Phase Report
- **Date**: Unknown
- **Reason for Archive**: Phase completion report
- **Value**: Historical project milestone documentation
- **Status**: Candidate for archival

**PHASE_4B_INDEX.md**
- **Type**: Phase Index
- **Date**: Unknown
- **Reason for Archive**: Phase-specific index
- **Value**: Reference for completed project phase
- **Status**: Candidate for archival

#### Working Documents

**DOCUMENTATION_FIX_CHECKLIST.md**
- **Type**: Working Checklist
- **Date**: Unknown
- **Reason for Archive**: If fixes are complete
- **Value**: Template for future documentation improvement efforts
- **Status**: Archive when checklist complete OR keep if ongoing

**DEVOPS_QUICK_REFERENCE.md**
- **Type**: Quick Reference
- **Date**: Unknown
- **Reason for Archive**: Only if superseded by better documentation
- **Value**: Operational reference
- **Status**: **Keep active** unless duplicate/outdated

### Currently Archived Documents

*No documents currently archived. This section will be populated as documents are moved to the archive.*

## How to Use This Archive

### For New Team Members

1. **Start with current documentation first** (see `/docs/README.md`)
2. **Consult archive for context** when you encounter:
   - Unexplained design decisions
   - Legacy code or configuration
   - References to past systems or approaches
3. **Don't rely on archived docs for current operations**

### For Existing Team Members

1. **Reference archived assessments** when planning similar work
2. **Review past decisions** to avoid repeating mistakes
3. **Use migration docs** as templates for future migrations
4. **Cite historical context** in new ADRs or proposals

### For Auditors and Compliance

1. **Security audit history** provides compliance trail
2. **Phase reports** document project governance
3. **Assessment reports** show continuous improvement
4. **Archived decisions** demonstrate due diligence

## Archival Process

### When to Archive a Document

Archive when ANY of these conditions are met:

1. **Feature/system described no longer exists**
   - Example: HTMX frontend documentation after React Native migration

2. **Assessment or audit is complete**
   - Example: Security audit after all findings remediated

3. **Project phase is finished**
   - Example: Phase 4B report after phase completion

4. **Decision has been superseded**
   - Example: Initial technology choice after migration to new tech

5. **Document has been replaced by newer version**
   - Example: Old deployment guide after Kubernetes adoption

### How to Archive a Document

**Step 1: Prepare the document**
```bash
# Add archival notice to top of document
```

Add this header to the archived document:

```markdown
# [Document Title]

> **ARCHIVED**: This document was archived on YYYY-MM-DD. It is preserved for historical reference only and may contain outdated information.
>
> **Reason for Archival**: [Brief explanation]
>
> **Superseded By**: [Link to replacement documentation, if applicable]
>
> **Last Active**: [Date when document was last actively used]

---

*Original content below*
```

**Step 2: Move the document**
```bash
# Move to archive directory
mv docs/DOCUMENT_NAME.md docs/archive/DOCUMENT_NAME.md

# Commit with explanation
git add docs/archive/DOCUMENT_NAME.md
git commit -m "docs: archive DOCUMENT_NAME (reason: completed assessment)"
```

**Step 3: Update this README**
- Move document from "Active Candidates" to "Currently Archived"
- Add entry with archival date and reason
- Update any cross-references

**Step 4: Update main documentation**
- Remove references from active documentation
- Add note in `/docs/README.md` if significant
- Update navigation/index files

### Archive Entry Template

When documenting an archived file, use this format:

```markdown
**DOCUMENT_NAME.md** (Archived: YYYY-MM-DD)
- **Original Location**: `/docs/path/to/file.md`
- **Type**: [Assessment Report | Migration Guide | Phase Report | etc.]
- **Date Range**: YYYY-MM-DD to YYYY-MM-DD
- **Reason**: [Brief explanation of why archived]
- **Superseded By**: [Link to replacement, if any]
- **Key Content**: [1-2 sentence summary]
- **Retrieval Notes**: [Any special considerations for using this archived doc]
```

## Archive Organization

Documents in this archive are organized by:

1. **Category subdirectories** (when archive grows):
   ```
   archive/
   ├── README.md (this file)
   ├── assessments/
   ├── migrations/
   ├── phase-reports/
   ├── deprecated-features/
   └── historical-decisions/
   ```

2. **Chronological naming** (when multiple versions):
   ```
   archive/assessments/
   ├── security-audit-2024-q1.md
   ├── security-audit-2024-q2.md
   └── security-audit-2024-q3.md
   ```

3. **Clear archival headers** (in every document)

## Retrieval and Reference

### Citing Archived Documents

When referencing archived documentation in current docs or code comments:

```markdown
See [archived security audit](../archive/SECURITY_AUDIT_REPORT.md) (archived 2024-11-23)
for historical context on authentication implementation.
```

### Searching the Archive

```bash
# Search all archived docs
grep -r "search term" docs/archive/

# List all archived files
find docs/archive/ -name "*.md" -type f

# Show recently archived
ls -lt docs/archive/*.md | head
```

## Archive Maintenance

### Quarterly Review

Every quarter, review:
1. Documents in main `/docs` directory for archival candidates
2. Archived documents for potential deletion (5+ years old, truly obsolete)
3. This README for accuracy and completeness
4. Cross-references from active documentation

### Deletion Policy

Documents may be **permanently deleted** from the archive when:
- More than 5 years old AND
- No compliance/audit requirement AND
- No historical value AND
- Approved by team lead

**Process:**
1. Propose deletion in team meeting
2. Get approval from at least 2 team members
3. Create backup before deletion
4. Document deletion in this README
5. Remove cross-references

### Backup Policy

Archived documentation is backed up along with the main repository:
- Git history preserves all versions
- Regular repository backups (per company policy)
- Consider exporting to separate backup for very old archives

---

## Related Documentation

- [Main Documentation Index](../README.md) - Current, active documentation
- [Contributing Guidelines](../../CONTRIBUTING.md) - How to contribute to documentation
- [Backend Architecture](../architecture/BACKEND_ARCHITECTURE.md) - Current system architecture

---

## Archive Statistics

**Total Archived Documents**: 0
**Last Archive Date**: N/A
**Last Review Date**: 2024-11-23
**Oldest Archive**: N/A
**Archive Size**: 0 MB

---

**Archive Maintained By**: Chores Tracker Documentation Team
**Last Updated**: November 23, 2024
**Next Review Due**: February 23, 2025 (Quarterly)
