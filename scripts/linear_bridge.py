#!/usr/bin/env python3
"""
Linear Bridge: Typed Python wrapper around linear-cli for Hermes, subagents, and scripts.
Enforces deterministic F5 Reality Gate protocol (--evidence for 'Done' transitions).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from dataclasses import dataclass
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch


@dataclass(frozen=True)
class LinearIssue:
    id: str
    title: str
    status: str
    url: str
    priority: int = 2
    description: str = ""


@dataclass(frozen=True)
class LinearProject:
    id: str
    name: str
    status: str


class LinearBridgeError(Exception):
    """Raised when linear-cli operations fail."""
    pass


class LinearBridge:
    """Typed bridge for interacting with Linear through linear-cli."""

    def __init__(self, cli_bin: Optional[str] = None, timeout_sec: int = 25):
        self.cli_bin = cli_bin or shutil.which("linear-cli") or "/usr/local/bin/linear-cli"
        self.timeout_sec = timeout_sec

    def _run_cli(self, args: List[str]) -> str:
        """Executes a linear-cli command safely with strict timeout."""
        if not os.path.exists(self.cli_bin) and not shutil.which(self.cli_bin):
            raise LinearBridgeError(f"linear-cli binary not found at: {self.cli_bin}")

        cmd = [self.cli_bin] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
                check=False
            )
        except subprocess.TimeoutExpired as exc:
            raise LinearBridgeError(f"Command '{' '.join(cmd)}' timed out after {self.timeout_sec}s") from exc
        except Exception as exc:
            raise LinearBridgeError(f"Failed to execute command '{' '.join(cmd)}': {exc}") from exc

        if result.returncode != 0:
            err_msg = result.stderr.strip() or result.stdout.strip()
            raise LinearBridgeError(f"linear-cli exited with code {result.returncode}: {err_msg}")

        return result.stdout.strip()

    def list_projects(self) -> List[LinearProject]:
        """Lists active projects in Linear."""
        output = self._run_cli(["projects"])
        projects: List[LinearProject] = []
        # Pattern: - Name [State: backlog] (ID: 3eb066b7...)
        pattern = re.compile(r"^-\s+(.+?)\s+\[State:\s*(.+?)\]\s+\(ID:\s*([a-f0-9-]+)\)", re.MULTILINE)
        for match in pattern.finditer(output):
            name, state, pid = match.groups()
            projects.append(LinearProject(id=pid.strip(), name=name.strip(), status=state.strip()))
        return projects

    def get_issue(self, issue_id: str) -> LinearIssue:
        """Retrieves issue details by ID."""
        clean_id = issue_id.strip().upper()
        output = self._run_cli(["issue", clean_id])

        # Pattern: [BAI-443] Title
        title_match = re.search(r"^\[([A-Z]+-\d+)\]\s+(.+)$", output, re.MULTILINE)
        status_match = re.search(r"Status:\s*([^|\n]+)", output)
        url_match = re.search(r"URL:\s*(https://[^\s]+)", output)
        priority_match = re.search(r"Priority:\s*(\d+)", output)

        if not title_match:
            raise LinearBridgeError(f"Could not parse issue details for {clean_id}: {output}")

        title = title_match.group(2).strip()
        status = status_match.group(1).strip() if status_match else "Unknown"
        url = url_match.group(1).strip() if url_match else ""
        priority = int(priority_match.group(1).strip()) if priority_match else 2

        # Extract description if present
        desc = ""
        if "Description:" in output:
            desc = output.split("Description:", 1)[1].strip()

        return LinearIssue(
            id=clean_id,
            title=title,
            status=status,
            url=url,
            priority=priority,
            description=desc
        )

    def create_issue(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        project_id: Optional[str] = None
    ) -> str:
        """Creates an issue in the active Linear project and returns the output/ID."""
        if not title.strip():
            raise ValueError("Issue title cannot be empty")

        args = ["create", title.strip()]
        if description:
            args.append(description.strip())
        if priority:
            args.extend(["--priority", str(priority)])
        if project_id:
            args.extend(["--project", project_id.strip()])

        return self._run_cli(args)

    def update_status(self, issue_id: str, status: str, evidence: str = "") -> bool:
        """
        Updates issue status. Enforces --evidence when setting status to 'Done'
        to respect the F5 Reality Gate.
        """
        clean_id = issue_id.strip().upper()
        clean_status = status.strip()

        if clean_status.lower() == "done" and not evidence.strip():
            raise ValueError(
                f"F5 Reality Gate Invariant: Transition to 'Done' requires non-empty --evidence for {clean_id}"
            )

        args = ["update-status", clean_id, clean_status]
        if evidence.strip():
            args.extend(["--evidence", evidence.strip()])

        self._run_cli(args)
        return True

    def add_comment(self, issue_id: str, comment: str) -> bool:
        """Adds a comment to an issue."""
        clean_id = issue_id.strip().upper()
        if not comment.strip():
            raise ValueError("Comment cannot be empty")

        self._run_cli(["comment", clean_id, comment.strip()])
        return True


# ==============================================================================
# Self-Test Suite (--test)
# ==============================================================================

class TestLinearBridge(unittest.TestCase):
    """Hermetic unit tests for LinearBridge."""

    def setUp(self):
        self.bridge = LinearBridge(cli_bin="/usr/local/bin/linear-cli")

    @patch.object(LinearBridge, "_run_cli")
    def test_list_projects_parsing(self, mock_run):
        mock_run.return_value = (
            "Projects:\n"
            "- Blindaje Soberano [State: backlog] (ID: 3eb066b7-485b-4aeb-8a07-3e4c9a01a890)\n"
            "- Brandbook Dual-Track [State: completed] (ID: 0b2f4950-95a3-4650-9aac-40ef4bc996b4)"
        )
        projects = self.bridge.list_projects()
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0].name, "Blindaje Soberano")
        self.assertEqual(projects[0].status, "backlog")
        self.assertEqual(projects[0].id, "3eb066b7-485b-4aeb-8a07-3e4c9a01a890")
        self.assertEqual(projects[1].name, "Brandbook Dual-Track")
        self.assertEqual(projects[1].status, "completed")

    @patch.object(LinearBridge, "_run_cli")
    def test_get_issue_parsing(self, mock_run):
        mock_run.return_value = (
            "[BAI-443] Bridge Python Tipado\n"
            "Status: In Progress | Priority: 2\n"
            "Team: Baiosfera (BAI) | Project: Blindaje Soberano\n"
            "URL: https://linear.app/baiosfera/issue/BAI-443/bridge\n"
            "Description:\n"
            "Modulo Python tipado para scripts."
        )
        issue = self.bridge.get_issue("bai-443")
        self.assertEqual(issue.id, "BAI-443")
        self.assertEqual(issue.title, "Bridge Python Tipado")
        self.assertEqual(issue.status, "In Progress")
        self.assertEqual(issue.priority, 2)
        self.assertEqual(issue.url, "https://linear.app/baiosfera/issue/BAI-443/bridge")
        self.assertIn("Modulo Python tipado", issue.description)

    @patch.object(LinearBridge, "_run_cli")
    def test_update_status_done_requires_evidence(self, mock_run):
        with self.assertRaises(ValueError) as ctx:
            self.bridge.update_status("BAI-443", "Done", evidence="")
        self.assertIn("F5 Reality Gate Invariant", str(ctx.exception))
        mock_run.assert_not_called()

    @patch.object(LinearBridge, "_run_cli")
    def test_update_status_done_with_evidence(self, mock_run):
        mock_run.return_value = "✅ Issue [BAI-443] status updated to: 'Done'"
        result = self.bridge.update_status("BAI-443", "Done", evidence="Tests passed exit 0")
        self.assertTrue(result)
        mock_run.assert_called_once_with(["update-status", "BAI-443", "Done", "--evidence", "Tests passed exit 0"])


def main():
    if "--test" in sys.argv:
        # Run test suite deterministically
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLinearBridge)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    print("LinearBridge: Typed Python wrapper for linear-cli. Use --test to run unit tests.")


if __name__ == "__main__":
    main()
