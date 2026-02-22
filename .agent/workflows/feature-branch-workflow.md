---
description: Standard workflow for feature branch development and Pull Requests
---

# Feature Branch Workflow

## Overview

This workflow guides you through creating a feature branch, making changes, and submitting a Pull Request with automated quality gates.

## Prerequisites

- Git installed and configured
- Repository cloned locally
- GitHub account with repository access
- Branch protection rules configured on `feature/v2-architecture`

## Step-by-Step Workflow

### 1. Start from Main

Always start from an up-to-date `feature/v2-architecture` branch:

```bash
git checkout feature/v2-architecture
git pull origin feature/v2-architecture
```

### 2. Create Feature Branch

Use descriptive branch names following the convention:

```bash
git checkout -b <type>/<description>
```

**Examples:**
- `git checkout -b feature/add-member-export`
- `git checkout -b fix/dataform-timestamp-bug`
- `git checkout -b docs/update-api-docs`

**Branch Types:**
- `feature/` - New features or enhancements
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates
- `chore/` - Maintenance tasks

### 3. Make Changes

Edit files, add features, fix bugs, etc.

### 4. Commit Changes

Use conventional commit messages:

```bash
git add .
git commit -m "feat: add member export functionality"
```

**Commit Message Prefixes:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions/updates
- `chore:` - Maintenance tasks

### 5. Push to GitHub

```bash
git push origin <your-branch-name>
```

### 6. Create Pull Request

**Option A: GitHub UI**
1. Go to repository on GitHub
2. Click "Compare & pull request" button
3. Fill in PR title and description
4. Click "Create pull request"

**Option B: Using MCP (via Antigravity)**
Ask Antigravity to create a PR:
```
"Create a PR from my feature branch to feature/v2-architecture with title 'Add member export' and description 'Implements CSV export for member data'"
```

### 7. Wait for Quality Gates

GitHub Actions will automatically run:
- ✅ **SonarQube Analysis** - Code quality and security
- ✅ **Test Coverage** - Ensures ≥80% coverage for new code
- ✅ **Dataform Compilation** - If `data/**` changed
- ✅ **Backend Tests** - If `backend/**` changed

**Check PR status:**
- Green checkmarks ✅ = All checks passed, ready to merge
- Red X ❌ = Checks failed, review errors and fix

### 8. Address Feedback

If quality gates fail:

**SonarQube Issues:**
- Review issues in SonarQube Cloud dashboard
- Use `/sonarqube-quality-gate` workflow for guidance
- Fix code smells, security vulnerabilities, or coverage gaps

**Test Failures:**
- Review test output in GitHub Actions logs
- Fix failing tests or add missing tests
- Run tests locally: `cd backend && pytest`

**Dataform Compilation Errors:**
- Review compilation errors in GitHub Actions logs
- Fix SQLX syntax or schema issues
- Test locally: `cd data && dataform compile`

**Push Fixes:**
```bash
git add .
git commit -m "fix: address SonarQube issues"
git push origin <your-branch-name>
```

Quality gates will re-run automatically.

### 9. Merge Pull Request

Once all checks pass:

1. Click "Merge pull request" on GitHub
2. Choose merge strategy:
   - **Squash and merge** (recommended) - Combines all commits into one
   - **Merge commit** - Preserves all commits
   - **Rebase and merge** - Linear history
3. Click "Confirm merge"
4. Delete the feature branch (GitHub will prompt)

### 10. Production Deployment

After merging to `feature/v2-architecture`, GitHub Actions will automatically:
- Deploy backend to Cloud Run (if `backend/**` changed)
- Run Dataform pipeline (if `data/**` changed)
- Run SonarQube analysis on `feature/v2-architecture`

**Monitor deployment:**
- Check GitHub Actions for deployment status
- Verify Cloud Run deployment in GCP Console
- Verify Dataform execution in BigQuery

### 11. Clean Up Local Branch

```bash
git checkout feature/v2-architecture
git pull origin feature/v2-architecture
git branch -d <your-branch-name>
```

## Quality Gates

All PRs must pass the following automated checks:

### SonarQube Quality Gate
- **Coverage:** ≥80% on new code
- **Duplications:** ≤3% on new code
- **Maintainability Rating:** A or B
- **Reliability Rating:** A
- **Security Rating:** A
- **Security Hotspots Reviewed:** 100%

### Test Coverage
- ≥80% coverage for new backend code
- All tests must pass
- Coverage validated by `check_coverage.py`

### Dataform Compilation
- All SQLX files must compile successfully
- No syntax errors
- Schema validation passes

### Backend Tests
- All pytest tests must pass
- No failing assertions
- Proper mocking of GCP services

## Troubleshooting

### "Branch protection rules prevent direct push to feature/v2-architecture"
✅ **Expected behavior.** Create a feature branch and PR instead.

### "Quality gate failed - coverage below 80%"
Add tests to increase coverage:
```bash
cd backend
pytest --cov=. --cov-report=term
```

### "SonarQube found security vulnerabilities"
Review issues in SonarQube Cloud and fix before merging.

### "Dataform compilation failed"
Check SQLX syntax and schema:
```bash
cd data
dataform compile
```

### "Cannot create PR - branch already exists"
Delete the old branch first:
```bash
git branch -D <branch-name>
git push origin --delete <branch-name>
```

## Best Practices

1. **Keep PRs Small:** Easier to review and less likely to have conflicts
2. **Write Descriptive Titles:** Clearly state what the PR does
3. **Add Context in Description:** Explain why the change is needed
4. **Link Related Issues:** Reference GitHub issues in PR description
5. **Respond to Feedback:** Address review comments promptly
6. **Keep Branch Updated:** Merge `feature/v2-architecture` into your branch if it's behind
7. **Delete Merged Branches:** Keep repository clean
8. **Test Locally First:** Run tests before pushing
9. **Follow Naming Convention:** Use proper branch type prefixes
10. **Write Good Commit Messages:** Use conventional commit format

## Branch Protection Rules

The `feature/v2-architecture` branch has the following protection rules:

- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging:
  - SonarQube Scan
  - SonarQube Quality Gate Check
  - Run Tests (backend)
  - Compile Dataform (data)
- ✅ Require conversation resolution before merging
- ❌ Direct pushes to `feature/v2-architecture` are blocked

## Related Workflows

- `/feature-development` - Complete feature development workflow
- `/sonarqube-quality-gate` - SonarQube analysis and quality gates
- `/data-pipeline-evolution` - Data pipeline changes
- `/mcp-integration` - Using MCP tools for GitHub and BigQuery
