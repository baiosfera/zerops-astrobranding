#!/usr/bin/env python3
"""Unit tests for AGENTS.md CUSTOM block synchronization & ZCP:BEGIN preservation."""
import os
import re
import subprocess
import tempfile
import unittest


class TestAgentsCustomSync(unittest.TestCase):
    def test_custom_block_sync_preserves_zcp_and_reflog(self):
        src_text = (
            "<!-- ZCP:BEGIN -->\n# Template ZCP Old\n<!-- ZCP:END -->\n\n"
            "<!-- CUSTOM:BEGIN -->\n## New Sovereign Section\nUpdated governance.\n<!-- CUSTOM:END -->\n"
        )
        dst_text = (
            "<!-- ZCP:BEGIN -->\n# Live Platform ZCP New (`zcp run`)\n<!-- ZCP:END -->\n\n"
            "<!-- CUSTOM:BEGIN -->\n## Old Custom Section\nOutdated.\n<!-- CUSTOM:END -->\n\n"
            "<!-- ZEROPS:REFLOG -->\n### Live Service Reflog\n<!-- /ZEROPS:REFLOG -->\n"
        )
        m_src = re.search(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", src_text, flags=re.S)
        self.assertIsNotNone(m_src)
        block = m_src.group(0)
        out = re.sub(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", lambda _: block, dst_text, count=1, flags=re.S)
        self.assertIn("# Live Platform ZCP New (`zcp run`)", out)
        self.assertIn("<!-- ZEROPS:REFLOG -->", out)
        self.assertIn("## New Sovereign Section", out)
        self.assertNotIn("## Old Custom Section", out)
        self.assertNotIn("# Template ZCP Old", out)

    def test_inject_agent_rule_preserves_targets(self):
        script = "/var/www/zerops-astrobranding/scripts/inject-agent-rule"
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "AGENTS.md")
            with open(target, "w", encoding="utf-8") as f:
                f.write(
                    "<!-- ZCP:BEGIN -->\n# Live ZCP\n<!-- ZCP:END -->\n\n"
                    "<!-- CUSTOM:BEGIN -->\n\n## Initial\nBody\n\n<!-- CUSTOM:END -->\n\n"
                    "<!-- ZEROPS:REFLOG -->\nref\n<!-- /ZEROPS:REFLOG -->\n"
                )
            res = subprocess.run(
                [script, "Appended Rule", "Test invariant.", target],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            with open(target, "r", encoding="utf-8") as rf:
                updated = rf.read()
            self.assertIn("# Live ZCP", updated)
            self.assertIn("<!-- ZEROPS:REFLOG -->", updated)
            self.assertIn("## Appended Rule", updated)


if __name__ == "__main__":
    unittest.main()
