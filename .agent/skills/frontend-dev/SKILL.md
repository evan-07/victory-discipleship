---
name: frontend-dev
description: Frontend implementation (HTML/CSS/JS - Static). Locked to Static Site Generation.
---

# Frontend Developer (Static Site)

## Mandate: Zero-Cost Static Hosting
**You are locked to "Static Site" generation to ensure zero-cost hosting on Cloudflare Pages.**

## Constraints
* **NO** Node.js runtime for the final build.
* **NO** Server-Side Rendering (SSR).
* **NO** Dynamic server requirements.
* **Output:** Pure HTML/CSS/JS.

## Workflow

### 0. Architectural Check (MANDATORY)
* **Start:** Before creating any new page or component, check `ARCHITECTURE.md` or consult `@architect`.
* **Goal:** Ensure no "clever" hacks (e.g., dynamic routing without a build step) violate the Zero-Cost rule.

### 1. Component Implementation
* Create/Modify HTML files in `frontend/`.
* **Tool:** Use `.agent/skills/frontend-dev/scripts/create_page.sh --help` to see scaffolding options.
* Style with CSS (Vanilla or Bootstrap 5 via CDN only). Tailwind is explicitly forbidden.
* Add interactivity with Vanilla JS.

### 2. Local Verification
* Ensure the site works by opening HTML files directly or using a simple static server.

### 3. Static Verification (NO Build Step)
* **There is NO build step.** Do NOT create or use `package.json`, `node_modules`, Vite, Webpack, or any other bundler for the frontend.
* Verify the site works by opening HTML files directly in a browser, or via `python -m http.server 3000` from the `frontend/` directory.
* Confirm the `frontend/` folder contains **only** `.html`, `.css`, and `.js` files before signoff.

## Tools
* **System:** `ls`, `cat`, `grep`
* **Scaffolding:** `.agent/skills/frontend-dev/scripts/create_page.sh`
* **SonarQube MCP & GitHub MCP:**
    * *Usage:* Use SonarQube MCP (`mcp_sonarqube_get_project_quality_gate_status`) for pre-flight quality checks. Use GitHub MCP (`mcp_github-mcp-...`) to manage feature branches and Pull Requests. See `.agent/workflows/mcp-integration.md`.
