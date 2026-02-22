---
description: How to run SonarQube analysis and check quality gates
---

# SonarQube Quality Gate Workflow

## When to Use
- Before creating a Pull Request
- After making code changes to `backend/` or `frontend/`
- When investigating code quality issues
- During code review

## Prerequisites
- SonarQube Cloud project configured for this repository
- `SONAR_TOKEN` secret configured in GitHub Actions
- MCP SonarQube server configured locally

## Steps

### 1. Trigger SonarQube Analysis (GitHub Actions)
SonarQube analysis runs automatically in GitHub Actions when:
- A Pull Request is created or updated
- Code is pushed to `feature/v2-architecture` branch

**Manual trigger:** Use GitHub Actions "Run workflow" button on the `SonarQube Analysis` workflow.

### 2. Check Quality Gate Status (MCP)
```
Use: mcp_sonarqube_get_project_quality_gate_status
Parameters:
  - projectKey: "evan-07_victory-discipleship"
  - branch: "feature/v2-architecture" (or PR branch name)
```

**Interpretation:**
- `status: "OK"` → Quality gate PASSED ✅
- `status: "ERROR"` → Quality gate FAILED ❌
- Check `conditions` array for specific failures (coverage, duplications, security, etc.)

### 3. Search for Issues (if Quality Gate Failed)
```
Use: mcp_sonarqube_search_sonar_issues_in_projects
Parameters:
  - projects: ["evan-07_victory-discipleship"]
  - branch: "your-branch-name"
  - issueStatuses: ["OPEN", "CONFIRMED"]
  - severities: ["BLOCKER", "CRITICAL", "MAJOR"]
```

**Prioritize:**
1. BLOCKER issues (must fix immediately)
2. CRITICAL security vulnerabilities
3. MAJOR code smells

### 4. Analyze Specific Code (Optional)
For new code not yet committed:
```
Use: mcp_sonarqube_analyze_code_snippet
Parameters:
  - projectKey: "evan-07_victory-discipleship"
  - codeSnippet: "<paste code here>"
  - language: "python" | "javascript"
```

### 5. Get Component Measures
To track metrics over time:
```
Use: mcp_sonarqube_get_component_measures
Parameters:
  - projectKey: "evan-07_victory-discipleship"
  - metricKeys: ["coverage", "code_smells", "security_hotspots", "bugs", "vulnerabilities"]
  - branch: "feature/v2-architecture"
```

### 6. Fix Issues
- Review issue details using `mcp_sonarqube_show_rule` with the rule key
- Make code changes to address issues
- Re-run analysis (push to PR branch)
- Verify quality gate passes

## Quality Gate Criteria (Default)
- **Coverage:** ≥80% on new code
- **Duplications:** ≤3% on new code
- **Maintainability Rating:** A or B
- **Reliability Rating:** A
- **Security Rating:** A
- **Security Hotspots Reviewed:** 100%

## Troubleshooting
- **"Project not found":** Verify `projectKey` matches SonarQube Cloud project
- **"Quality gate not found":** Ensure SonarQube analysis has run at least once
- **"Branch not found":** Check branch name matches exactly (case-sensitive)
