#!/usr/bin/env python3
"""
Documentation Impact Checker

Analyzes git diff to determine if ARCHITECTURE.md or README.md need updates based on
the routing matrix defined in .agent/rules/persistence.md and README.md Section 3.

Usage:
    python3 check_docs_impact.py [--base BASE_REF] [--head HEAD_REF]

Examples:
    # Check changes in current working tree
    python3 check_docs_impact.py

    # Check changes between specific commits
    python3 check_docs_impact.py --base origin/main --head HEAD

    # Check changes in a specific commit
    python3 check_docs_impact.py --base abc123^ --head abc123
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Set


class DocumentationImpactChecker:
    """Checks if code changes require documentation updates."""

    # Trigger rules based on file paths
    TRIGGERS = {
        "ARCHITECTURE.md#7": {
            "description": "Backend API Routes",
            "paths": ["backend/"],
            "keywords": ["@app.post", "@app.get", "@app.put", "@app.delete", "router.post", "router.get"],
        },
        "ARCHITECTURE.md#6": {
            "description": "Frontend Components",
            "paths": ["frontend/"],
            "extensions": [".html"],
            "exclude": ["index.html"],  # Only new pages, not modifications to existing
        },
        "ARCHITECTURE.md#8": {
            "description": "Data Architecture",
            "paths": ["data/definitions/"],
            "extensions": [".sqlx"],
        },
        "ARCHITECTURE.md#10": {
            "description": "Terraform Infrastructure",
            "paths": ["terraform/"],
            "extensions": [".tf"],
            "keywords": ["resource"],
        },
        "README.md#6": {
            "description": "Deployment & Secrets (workflows)",
            "paths": [".github/workflows/"],
            "extensions": [".yaml", ".yml"],
        },
        "README.md#3": {
            "description": "Agent Orchestration (workflows)",
            "paths": [".agent/workflows/"],
            "extensions": [".md"],
        },
    }

    def __init__(self, base_ref: str = None, head_ref: str = None):
        """Initialize the checker with git references."""
        self.base_ref = base_ref
        self.head_ref = head_ref
        self.repo_root = self._get_repo_root()

    def _get_repo_root(self) -> Path:
        """Get the git repository root directory."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            )
            return Path(result.stdout.strip())
        except subprocess.CalledProcessError:
            print("ERROR: Not in a git repository", file=sys.stderr)
            sys.exit(1)

    def _get_changed_files(self) -> List[str]:
        """Get list of changed files."""
        cmd = ["git", "diff", "--name-status"]

        if self.base_ref and self.head_ref:
            cmd.extend([self.base_ref, self.head_ref])
        elif self.base_ref:
            cmd.append(self.base_ref)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            changes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status, filepath = parts[0], parts[1]
                    changes.append((status, filepath))
            return changes
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to get git diff: {e}", file=sys.stderr)
            sys.exit(1)

    def _get_file_content_changes(self, filepath: str) -> str:
        """Get the diff content for a specific file."""
        cmd = ["git", "diff"]

        if self.base_ref and self.head_ref:
            cmd.extend([self.base_ref, self.head_ref, "--", filepath])
        elif self.base_ref:
            cmd.extend([self.base_ref, "--", filepath])
        else:
            cmd.extend(["--", filepath])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def check_impact(self) -> Dict[str, List[str]]:
        """
        Check if documentation updates are required.

        Returns:
            Dict mapping documentation sections to reasons for update
        """
        changes = self._get_changed_files()
        impacts = {}

        for status, filepath in changes:
            # Skip deletions for documentation impact
            if status.startswith("D"):
                continue

            # Check against each trigger rule
            for doc_section, rule in self.TRIGGERS.items():
                reasons = []

                # Check if file path matches
                path_matches = any(filepath.startswith(path) for path in rule["paths"])
                if not path_matches:
                    continue

                # Check file extension if specified
                if "extensions" in rule:
                    ext = Path(filepath).suffix
                    if ext not in rule["extensions"]:
                        continue

                # Check exclusions
                if "exclude" in rule:
                    filename = Path(filepath).name
                    if filename in rule["exclude"]:
                        continue

                # For new files, always trigger
                if status.startswith("A"):
                    reason = f"New file: {filepath}"
                    reasons.append(reason)

                # Check for keywords in diff content
                if "keywords" in rule and status.startswith("M"):
                    diff_content = self._get_file_content_changes(filepath)
                    for keyword in rule["keywords"]:
                        if keyword in diff_content:
                            # Check if it's an addition (line starts with +)
                            for line in diff_content.split("\n"):
                                if line.startswith("+") and keyword in line:
                                    reason = f"Modified file with '{keyword}': {filepath}"
                                    reasons.append(reason)
                                    break

                # If we found reasons, add to impacts
                if reasons:
                    if doc_section not in impacts:
                        impacts[doc_section] = []
                    impacts[doc_section].extend(reasons)

        return impacts

    def format_report(self, impacts: Dict[str, List[str]]) -> str:
        """Format the impact report for output."""
        if not impacts:
            return "✅ PASS: No documentation updates required based on current changes."

        report_lines = ["⚠️  REQUIRES_UPDATE: Documentation updates needed", ""]

        for doc_section, reasons in sorted(impacts.items()):
            doc_file, section_anchor = doc_section.split("#")
            rule = self.TRIGGERS[doc_section]

            report_lines.append(f"📄 {doc_file} (Section {section_anchor}: {rule['description']})")
            for reason in reasons:
                report_lines.append(f"   - {reason}")
            report_lines.append("")

        report_lines.append("Action Required:")
        report_lines.append("  1. Update the documentation sections listed above")
        report_lines.append("  2. Ensure cross-references between README.md and ARCHITECTURE.md are consistent")
        report_lines.append("  3. Run check_links.py to validate all links")

        return "\n".join(report_lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check if code changes require documentation updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base",
        help="Base git reference for comparison (e.g., origin/main, abc123^)",
        default=None,
    )
    parser.add_argument(
        "--head",
        help="Head git reference for comparison (e.g., HEAD, abc123)",
        default=None,
    )

    args = parser.parse_args()

    checker = DocumentationImpactChecker(base_ref=args.base, head_ref=args.head)
    impacts = checker.check_impact()
    report = checker.format_report(impacts)

    print(report)

    # Exit with non-zero if updates required
    sys.exit(1 if impacts else 0)


if __name__ == "__main__":
    main()
