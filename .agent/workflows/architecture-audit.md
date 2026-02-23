---
description: Complete workflow for architecture compliance audits, from execution to remediation
---

# Architecture Compliance Audit Workflow

This workflow provides a systematic approach to auditing the codebase against ARCHITECTURE.md standards, identifying violations, implementing remediations, and tracking future improvements.

## When to Use This Workflow

- **Scheduled Audits**: Run quarterly or before major releases
- **Post-Feature Implementation**: Verify new features comply with standards
- **Onboarding**: Help new team members understand architectural standards
- **Pre-Production**: Final compliance check before production deployments

---

## Phase 1: Pre-Flight Checks

### 1. Review governing documents
```bash
# Read in order
cat README.md
cat ARCHITECTURE.md
cat .agent/rules/persistence.md
```

### 2. Capture current repository state
// turbo
```bash
cd /path/to/victory-discipleship
git status
git diff --stat
```

### 3. Create audit artifacts directory
Artifacts will be created automatically in brain directory, but prepare to reference:
- `task.md` - Audit phase checklist
- `implementation_plan.md` - Audit methodology
- `audit_report.md` - Findings and violations
- `walkthrough.md` - Remediation proof of work

---

## Phase 2: Execute Automated Checks

### 4. Run validation scripts
// turbo
```bash
# Structure validation
python3 .agent/skills/architect/scripts/validate_structure.py

# Cost validation
bash .agent/skills/infra-ops/scripts/cost_sentinel.sh

# Test coverage
python3 .agent/skills/qa-engineer/scripts/check_coverage.py

# Documentation links
python3 .agent/skills/readme-updater/scripts/check_links.py

# Documentation impact
python3 .agent/skills/readme-updater/scripts/check_docs_impact.py

# Schema validation (if exists)
python3 .agent/skills/data-engineer/scripts/schema_lint.py 2>/dev/null || echo "schema_lint.py not found"
```

**Record Results**: Note any PASS/FAIL for each script

---

## Phase 3: Search for Prohibited Patterns

### 5. Check for local execution commands
// turbo
```bash
# Search documentation for prohibited commands
grep -rn "python main.py\|uvicorn\|fastapi dev\|npm start" README.md ARCHITECTURE.md .agent/ 2>/dev/null | grep -v "NEVER suggest" || echo "PASS: No local execution instructions"

# Check for manual terraform apply
grep -rn "terraform apply" README.md ARCHITECTURE.md .agent/workflows/ 2>/dev/null | grep -v "GitHub Actions" || echo "PASS: No manual terraform apply"

# Check for local dataform run
grep -rn "dataform run" README.md ARCHITECTURE.md .agent/workflows/ 2>/dev/null | grep -v "GitHub Actions" || echo "PASS: No local dataform run"
```

---

## Phase 4: Manual Code & Configuration Review

### 6. Inspect critical paths
Review these areas manually:

**GitHub Workflows**:
```bash
ls -la .github/workflows/
# Check each workflow for:
# - WIF vs credentials_json usage
# - Consistent authentication patterns
# - No manual deployment steps
```

**Backend Implementation**:
```bash
# Verify framework matches docs
head -20 backend/main.py
# Check: Flask vs FastAPI vs other
```

**Data Pipeline**:
```bash
# Verify medallion structure
ls -R data/definitions/
# Check: 1_bronze, 2_silver, 3_gold structure
# Verify partitioning strategy
```

**Agent Skills**:
```bash
# Verify all skills reference ARCHITECTURE.md
grep -l "ARCHITECTURE.md" .agent/skills/*/SKILL.md
```

---

## Phase 5: Compile Audit Report

### 7. Create structured findings document
Create `audit_report.md` with:

**Structure**:
```markdown
# Architecture Compliance Audit Report

## Executive Summary
- Overall compliance: GOOD/FAIR/POOR
- Total violations: count by severity
- Key findings summary

## Violations Found

### Critical Priority
(Issues that break core principles)

### High Priority  
(Missing tests, security gaps)

### Medium Priority
(Inconsistencies, documentation gaps)

### Low Priority
(Nice-to-have improvements)

## Positive Findings
(Areas of excellent compliance)

## Remediation Plan
Prioritized actions with owners and effort estimates
```

---

## Phase 6: Suggest & Prioritize Remediations

### 8. Categorize violations by priority

**Critical** (Fix immediately):
- Security vulnerabilities
- Data integrity issues
- Production-breaking changes

**High** (Fix before next release):
- Missing tests for critical functions
- Major documentation gaps
- Broken automation

**Medium** (Fix within sprint):
- Inconsistent patterns
- Minor documentation updates
- Non-critical tooling gaps

**Low** (Schedule for future):
- Nice-to-have scripts
- Optional optimizations
- Enhancement opportunities

### 9. Create remediation steps document
For each violation, document:
- **Objective**: What needs to be fixed
- **Steps**: Specific commands/changes
- **Verification**: How to confirm fix
- **Effort**: Time estimate

---

## Phase 7: Implement Remediations

### 10. Work through prioritized list
Start with Critical/High priority:

**For each remediation**:
1. Create feature branch (optional for small fixes)
2. Implement fix
3. Run relevant validation scripts
4. Verify fix resolves issue
5. Document in walkthrough

**Example - Missing Tests**:
```bash
# 1. Create test file
touch backend/tests/test_<module>.py

# 2. Write tests
# ... (implement tests)

# 3. Verify coverage
python3 .agent/skills/qa-engineer/scripts/check_coverage.py
```

**Example - Documentation Update**:
```bash
# 1. Update docs
# Edit ARCHITECTURE.md or README.md

# 2. Verify links
python3 .agent/skills/readme-updater/scripts/check_links.py
```

---

## Phase 8: Track Unaddressed Items

### 11. Update FUTURE_IMPROVEMENTS.md
For violations NOT immediately fixed (usually Low priority or deferred Medium):

```markdown
### 🔧 [Issue Name] (Priority: Low/Medium/High)
**Current State**: Description of violation

**Issue Identified**: Architecture Audit YYYY-MM-DD found...

**Proposed Enhancement**:
- Specific steps to fix
- Code snippets or examples

**Benefits**:
- ✅ Compliance improvement
- ✅ Other benefits

**Effort**: Time estimate

**Reference**: 
- Audit Report: `audit_report.md` ([Priority] Violation #N)
- Related files/workflows
```

---

## Phase 9: Verification & Sign-Off

### 12. Re-run all validation scripts
// turbo
```bash
# Confirm all scripts now pass (or expected failures documented)
python3 .agent/skills/architect/scripts/validate_structure.py && \
python3 .agent/skills/qa-engineer/scripts/check_coverage.py && \
python3 .agent/skills/readme-updater/scripts/check_links.py && \
bash .agent/skills/infra-ops/scripts/cost_sentinel.sh
```

### 13. Create walkthrough artifact
Document in `walkthrough.md`:
- Changes made
- Tests performed
- Validation results
- Before/after metrics
- Outstanding items in FUTURE_IMPROVEMENTS.md

### 14. Review git changes
// turbo
```bash
git status
git diff --stat
```

---

## Phase 10: Commit & Close

### 15. Commit remediation changes
```bash
git add .
git commit -m "fix: architecture compliance remediations

- Added backend tests for [functions]
- Updated documentation to reflect [changes]
- Created [new scripts/tools]
- Tracked deferred items in FUTURE_IMPROVEMENTS.md

Resolves: [violations]
Deferred: [violations] tracked in FUTURE_IMPROVEMENTS.md"
```

### 16. Push and create PR (if using branches)
```bash
git push origin audit-remediation-YYYY-MM-DD
# Create PR with audit_report.md and walkthrough.md linked
```

---

## Success Criteria

**Audit is complete when**:
- ✅ All automated validation scripts executed
- ✅ Audit report created with categorized violations
- ✅ High/Critical violations remediated OR justified in report
- ✅ Medium/Low violations either fixed OR tracked in FUTURE_IMPROVEMENTS.md
- ✅ Walkthrough artifact documents all changes
- ✅ All validation scripts pass (or expected failures documented)
- ✅ Changes committed to repository

---

## Tips & Best Practices

1. **Don't skip automated checks**: They catch 80% of issues quickly
2. **Document as you go**: Don't wait until end to create audit report
3. **Fix in priority order**: Don't let perfect be enemy of good
4. **Update FUTURE_IMPROVEMENTS.md**: Track deferrals for transparency
5. **Involve appropriate agents**: Route findings to @architect, @qa-engineer, etc.
6. **Re-audit after major features**: Don't let compliance drift

---

## Related Workflows

- `/feature-development` - Use audit to validate new features
- `/data-pipeline-evolution` - Audit schema changes against medallion architecture

---

## Agent Coordination

This workflow typically involves:
- **@orchestrator**: Coordinates overall audit process
- **@architect**: Reviews structural findings, validates remediation plans
- **@qa-engineer**: Handles test coverage violations
- **@infra-ops**: Addresses infrastructure/cost/terraform issues
- **@data-engineer**: Fixes data pipeline violations
- **@readme-updater**: Remediates documentation gaps
