# Current Plan Artifact (CPA)

## Phase
EXECUTION

## Goal
Integrate SonarQube MCP into the Victory Discipleship Member Management System to establish automated code quality governance, security scanning, and technical debt tracking.

## Non-negotiables
- Maintain Free Tier constraints (SonarQube Cloud Free Tier)
- Follow GitOps principles (no manual deployments)
- No local execution of quality gates
- All quality checks via GitHub Actions
- MCP tools read-only by default (write operations require user approval)

## Affected Paths
- `.agent/rules/persistence.md` (Tool authorization + quality governance)
- `ARCHITECTURE.md` (Technology stack, DoD, documentation triggers)
- `README.md` (Agent responsibilities, workflows, secrets)
- `.agent/skills/qa-engineer/SKILL.md` (SonarQube tools and workflow)
- `.agent/workflows/sonarqube-quality-gate.md` (NEW - workflow documentation)
- `.github/workflows/sonarqube-analysis.yaml` (NEW - CI/CD integration)
- `sonar-project.properties` (NEW - SonarQube configuration)

## Mandatory Agents
- `@architect` - Review ARCHITECTURE.md changes for compliance
- `@qa-engineer` - Update SKILL.md with SonarQube MCP tools
- `@readme-updater` - Update README.md and verify documentation links
- `@infra-ops` - Review GitHub Actions workflow for cost/security

## Documentation Impact
- **persistence.md**: Add SonarQube MCP tools to authorization whitelist; add Section 12 for code quality governance
- **ARCHITECTURE.md**: Add SonarQube to technology stack; update DoD with quality gate requirement; add documentation trigger for quality gate changes
- **README.md**: Update @qa-engineer responsibilities; add /sonarqube-quality-gate workflow; add GitHub Secrets for SonarQube
- **qa-engineer/SKILL.md**: Add SonarQube MCP tools and updated workflow

## Architect Valid Plan
**Status:** APPROVED BY USER

**Implementation Strategy:**
1. Update governance rules (persistence.md) with SonarQube tool authorization
2. Update architecture documentation (ARCHITECTURE.md) with SonarQube integration
3. Update README.md with agent responsibilities and workflow references
4. Update @qa-engineer SKILL.md with SonarQube MCP tools
5. Create /sonarqube-quality-gate workflow documentation
6. Create GitHub Actions workflow for SonarQube analysis
7. Create sonar-project.properties configuration file

**Quality Gates:**
- SonarQube Quality Gate must PASS for all PRs
- Coverage: ≥80% on new code
- Security: Zero "Blocker" or "Critical" vulnerabilities
- Maintainability: "A" or "B" rating required

## Steps + Owners
1. **@orchestrator**: Update persistence.md with tool authorization ⏳
2. **@orchestrator**: Update ARCHITECTURE.md with SonarQube integration ⏳
3. **@readme-updater**: Update README.md with workflows and secrets ⏳
4. **@qa-engineer**: Update SKILL.md with SonarQube tools ⏳
5. **@orchestrator**: Create /sonarqube-quality-gate workflow ⏳
6. **@infra-ops**: Review GitHub Actions workflow ⏳
7. **@orchestrator**: Create sonar-project.properties ⏳
8. **@readme-updater**: Verify documentation links ⏳

## Verification Plan
1. **Documentation validation**: Run `check_links.py` to verify all links
2. **Workflow syntax**: Validate GitHub Actions YAML syntax
3. **MCP tool testing**: Test SonarQube MCP connection (requires project creation by user)
4. **User manual testing**: User creates SonarQube project and tests GitHub Actions workflow