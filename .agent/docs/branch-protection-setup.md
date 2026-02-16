# Branch Protection Setup Guide

## Overview

This guide provides step-by-step instructions for configuring branch protection rules on the `main` branch to enforce the feature branch workflow.

## Prerequisites

- Repository admin access on GitHub
- All GitHub Actions workflows deployed and tested

## Setup Instructions

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository: https://github.com/evan-07/victory-discipleship
2. Click **Settings** (top navigation)
3. Click **Branches** (left sidebar under "Code and automation")
4. Click **Add branch protection rule**

### 2. Configure Branch Name Pattern

- **Branch name pattern:** `main`

This will apply the protection rules to the `main` branch only.

### 3. Enable Pull Request Requirements

✅ **Check:** "Require a pull request before merging"

**Sub-options:**
- **Required number of approvals before merging:** `0` (or `1` if you want self-review)
  - Set to `0` for solo development
  - Set to `1` if you want to enforce self-review before merging
- ✅ **Check:** "Dismiss stale pull request approvals when new commits are pushed"
  - This ensures that new commits require re-approval
- ❌ **Uncheck:** "Require review from Code Owners"
  - Not needed for solo development

### 4. Enable Status Check Requirements

✅ **Check:** "Require status checks to pass before merging"

**Sub-options:**
- ✅ **Check:** "Require branches to be up to date before merging"
  - This ensures PRs are tested against the latest `main`

**Status checks that are required:**

Click "Search for status checks" and add the following:
- `SonarQube Scan` (from `sonarqube-analysis.yaml`)
- `SonarQube Quality Gate Check` (from `sonarqube-analysis.yaml`)
- `Run Tests` (from `deploy_backend.yaml`)
- `Compile Dataform` (from `dataform.yaml`)

> [!NOTE]
> Status checks will only appear in the list after they have run at least once. You may need to create a test PR first to populate this list.

### 5. Enable Conversation Resolution (Optional)

✅ **Check:** "Require conversation resolution before merging" (recommended)

This ensures all review comments are addressed before merging.

### 6. Additional Settings (Optional)

**Recommended:**
- ❌ **Uncheck:** "Require deployments to succeed before merging"
  - Not applicable for this workflow
- ❌ **Uncheck:** "Require signed commits"
  - Optional, but not required for this project
- ❌ **Uncheck:** "Require linear history"
  - Optional, allows merge commits
- ❌ **Uncheck:** "Lock branch"
  - Would prevent all changes, not desired

**Bypass Settings:**
- ❌ **Uncheck:** "Do not allow bypassing the above settings"
  - Recommended to keep unchecked so you can bypass in emergencies
- ❌ **Uncheck:** "Allow force pushes"
  - Keep disabled to prevent history rewriting
- ❌ **Uncheck:** "Allow deletions"
  - Keep disabled to prevent accidental branch deletion

### 7. Save Protection Rules

Click **Create** (or **Save changes** if editing existing rules)

## Verification

### Test 1: Direct Push to Main (Should Fail)

```bash
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "test: direct push"
git push origin main
```

**Expected Result:**
```
remote: error: GH006: Protected branch update failed for refs/heads/main.
remote: error: Changes must be made through a pull request.
```

✅ If you see this error, branch protection is working correctly!

### Test 2: Feature Branch Workflow (Should Succeed)

```bash
# Create feature branch
git checkout -b test/branch-protection
echo "test" >> README.md
git add README.md
git commit -m "test: branch protection"
git push origin test/branch-protection
```

**Expected Result:**
- Push succeeds
- GitHub shows "Compare & pull request" button
- Creating PR triggers quality gates

✅ If you can create a PR and see status checks running, the workflow is configured correctly!

### Test 3: Quality Gates (Should Block Merge)

1. Create a PR with intentionally failing code (e.g., remove a test)
2. Verify that the PR shows:
   - ❌ Red X next to failing status check
   - "Merging is blocked" message
   - Cannot click "Merge pull request" button

✅ If merge is blocked when checks fail, quality gates are working!

### Test 4: Successful Merge (Should Deploy)

1. Create a PR with passing code
2. Wait for all status checks to pass (green checkmarks)
3. Click "Merge pull request"
4. Verify:
   - PR merges successfully
   - GitHub Actions triggers deployment workflows
   - Changes appear in production

✅ If deployment triggers after merge, the complete workflow is functional!

## Troubleshooting

### "Status checks not appearing in the list"

**Solution:** Create a test PR first to trigger the workflows. Status checks only appear after they've run at least once.

```bash
git checkout -b test/initial-pr
echo "# Test" >> test.md
git add test.md
git commit -m "test: initial PR for status checks"
git push origin test/initial-pr
```

Create a PR, wait for workflows to run, then go back to branch protection settings.

### "Cannot push to main even with protection disabled"

**Solution:** Check if you have other branch protection rules or organization-level restrictions.

1. Go to Settings → Branches
2. Verify no other rules apply to `main`
3. Check organization settings if applicable

### "Quality gates not running on PR"

**Solution:** Verify workflow triggers are correct.

1. Check `.github/workflows/*.yaml` files have `pull_request:` triggers
2. Verify workflows are enabled in Actions tab
3. Check workflow run logs for errors

### "Merge button greyed out even with passing checks"

**Solution:** Ensure all required status checks are passing.

1. Scroll down to "All checks have passed" section
2. Verify each required check has a green checkmark
3. If any are pending, wait for them to complete
4. If any failed, fix the issues and push again

## Rollback Instructions

If you need to disable branch protection:

1. Go to Settings → Branches
2. Find the `main` branch protection rule
3. Click **Delete** (trash icon)
4. Confirm deletion

This will allow direct pushes to `main` again.

## Summary

After completing this setup:
- ✅ Direct pushes to `main` are blocked
- ✅ All changes must go through Pull Requests
- ✅ PRs must pass quality gates before merging
- ✅ Merging to `main` triggers production deployment
- ✅ Feature branch workflow is fully enforced

## Related Documentation

- `/feature-branch-workflow` - Complete feature branch workflow guide
- `/sonarqube-quality-gate` - SonarQube quality gate details
- `ARCHITECTURE.md` - Feature branch workflow governance rules
- `README.md` - Quick reference for creating feature branches
