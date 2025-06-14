#!/usr/bin/env python3
"""
Simple Dockerfile linter for RAFT Toolkit.

Checks for common Dockerfile best practices and issues.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DockerfileLinter:
    """Simple Dockerfile linter."""

    def __init__(self, dockerfile_path: str):
        self.dockerfile_path = Path(dockerfile_path)
        self.lines = []
        self.issues = []

    def load_dockerfile(self) -> bool:
        """Load Dockerfile content."""
        try:
            with open(self.dockerfile_path, "r") as f:
                self.lines = f.readlines()
            return True
        except FileNotFoundError:
            print(f"❌ Dockerfile not found: {self.dockerfile_path}")
            return False
        except Exception as e:
            print(f"❌ Error reading Dockerfile: {e}")
            return False

    def check_from_casing(self) -> None:
        """Check for consistent FROM/AS casing."""
        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if re.match(r"^FROM\s+", line, re.IGNORECASE):
                if " as " in line:  # lowercase 'as'
                    self.issues.append(
                        (i, "FromAsCasing", "'as' should be uppercase 'AS' to match 'FROM'", line.strip())
                    )
                elif re.search(r"\s+as\s+", line):  # mixed case
                    self.issues.append((i, "FromAsCasing", "Use consistent uppercase: 'FROM ... AS ...'", line.strip()))

    def check_labels(self) -> None:
        """Check for proper labeling."""
        has_maintainer = False
        has_description = False

        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if re.match(r"^LABEL\s+", line, re.IGNORECASE):
                if "maintainer" in line.lower():
                    has_maintainer = True
                if "description" in line.lower():
                    has_description = True

        if not has_maintainer:
            self.issues.append((0, "MissingLabel", "Consider adding LABEL maintainer", ""))
        if not has_description:
            self.issues.append((0, "MissingLabel", "Consider adding LABEL description", ""))

    def check_user_security(self) -> None:
        """Check for proper user handling."""
        switches_to_user = False
        creates_user = False

        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if re.match(r"^USER\s+", line, re.IGNORECASE):
                switches_to_user = True
            if "useradd" in line or "adduser" in line:
                creates_user = True

        if not switches_to_user:
            self.issues.append((0, "SecurityIssue", "Consider using USER instruction for security", ""))
        elif not creates_user:
            self.issues.append((0, "SecurityWarning", "USER instruction found but no user creation detected", ""))

    def check_run_best_practices(self) -> None:
        """Check RUN instruction best practices."""
        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if re.match(r"^RUN\s+", line, re.IGNORECASE):
                # Check for apt-get without update
                if "apt-get install" in line and "apt-get update" not in line:
                    # Check previous lines for apt-get update
                    context_lines = self.lines[max(0, i - 3) : i - 1]
                    has_update = any("apt-get update" in l for l in context_lines)
                    if not has_update:
                        self.issues.append(
                            (i, "AptGetUpdate", "apt-get install should be preceded by apt-get update", line.strip())
                        )

                # Check for rm -rf /var/lib/apt/lists/*
                if "apt-get" in line and "rm -rf /var/lib/apt/lists/*" not in line:
                    # Check if it's in the same RUN block
                    if not any(
                        "rm -rf /var/lib/apt/lists/*" in l for l in self.lines[i - 1 : min(len(self.lines), i + 5)]
                    ):
                        self.issues.append(
                            (i, "AptCacheCleanup", "Consider cleaning apt cache after apt-get", line.strip())
                        )

    def check_copy_best_practices(self) -> None:
        """Check COPY instruction best practices."""
        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if re.match(r"^COPY\s+", line, re.IGNORECASE):
                # Check for copying everything (COPY . .)
                if re.search(r"COPY\s+\.\s+\.", line):
                    self.issues.append(
                        (
                            i,
                            "CopyAll",
                            "Consider using .dockerignore or specific paths instead of 'COPY . .'",
                            line.strip(),
                        )
                    )

    def check_env_best_practices(self) -> None:
        """Check ENV instruction best practices."""
        for i, line in enumerate(self.lines, 1):
            line = line.strip()
            if re.match(r"^ENV\s+", line, re.IGNORECASE):
                # Check for multiple ENV instructions that could be combined
                pass  # This would require more complex analysis

    def run_checks(self) -> bool:
        """Run all checks."""
        if not self.load_dockerfile():
            return False

        checks = [
            ("FROM/AS Casing", self.check_from_casing),
            ("Labels", self.check_labels),
            ("User Security", self.check_user_security),
            ("RUN Best Practices", self.check_run_best_practices),
            ("COPY Best Practices", self.check_copy_best_practices),
            ("ENV Best Practices", self.check_env_best_practices),
        ]

        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                print(f"⚠️ Error during {check_name} check: {e}")

        return True

    def report_issues(self) -> None:
        """Report all found issues."""
        if not self.issues:
            print("🎉 No linting issues found!")
            return

        print(f"📋 Found {len(self.issues)} linting issues:")
        print()

        # Group issues by type
        issues_by_type = {}
        for line_num, issue_type, message, context in self.issues:
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append((line_num, message, context))

        for issue_type, issues in issues_by_type.items():
            print(f"🔍 {issue_type}:")
            for line_num, message, context in issues:
                if line_num > 0:
                    print(f"  Line {line_num}: {message}")
                    if context:
                        print(f"    -> {context}")
                else:
                    print(f"  {message}")
            print()

    def get_summary(self) -> Dict[str, int]:
        """Get summary of issues."""
        summary = {}
        for _, issue_type, _, _ in self.issues:
            summary[issue_type] = summary.get(issue_type, 0) + 1
        return summary


def main():
    """Main function."""
    dockerfile_path = sys.argv[1] if len(sys.argv) > 1 else "Dockerfile"

    print("🐳 RAFT Toolkit Dockerfile Linter")
    print("=" * 40)
    print(f"Checking: {dockerfile_path}")
    print()

    linter = DockerfileLinter(dockerfile_path)

    if not linter.run_checks():
        sys.exit(1)

    linter.report_issues()

    summary = linter.get_summary()
    if summary:
        print("📊 Issue Summary:")
        for issue_type, count in summary.items():
            print(f"  {issue_type}: {count}")
        print()

        # Determine exit code based on issue severity
        critical_issues = sum(
            count for issue_type, count in summary.items() if issue_type in ["FromAsCasing", "SecurityIssue"]
        )

        if critical_issues > 0:
            print(f"❌ {critical_issues} critical issues found")
            sys.exit(1)
        else:
            print("⚠️ Only warnings found")
            sys.exit(0)
    else:
        print("✅ Dockerfile follows best practices!")
        sys.exit(0)


if __name__ == "__main__":
    main()
