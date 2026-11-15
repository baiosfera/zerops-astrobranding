#!/usr/bin/env python3
"""Unit tests for zcp-preflight-gate.sh (self-shadowing & unresolved service refs)."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

GATE_SCRIPT = Path(__file__).resolve().parent.parent / "zcp-preflight-gate.sh"


class TestPreflightGate(unittest.TestCase):
    def _run_gate(self, yaml_content: str, extra_args=None, env_override=None):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tf:
            tf.write(yaml_content)
            tmp_path = tf.name
        try:
            env = os.environ.copy()
            env.pop("PROJECT_NAME", None)
            for k in list(env.keys()):
                if k.endswith(("_hostname", "_connectionString", "_serviceId")):
                    env.pop(k, None)
            if env_override:
                env.update(env_override)
            cmd = ["bash", str(GATE_SCRIPT)]
            if extra_args:
                cmd.extend(extra_args)
            cmd.append(tmp_path)
            return subprocess.run(cmd, capture_output=True, text=True, env=env)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_rejects_same_key_self_shadowing(self):
        res = self._run_gate(
            """
zerops:
  - setup: webdev
    run:
      base: ubuntu/bun@1.3
      envVariables:
        PAYMENT_PUBLIC_KEY: ${PAYMENT_PUBLIC_KEY}
"""
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Self-shadowing ilegal", res.stdout)

    def test_allows_distinct_vault_key(self):
        res = self._run_gate(
            """
zerops:
  - setup: webdev
    run:
      base: ubuntu/bun@1.3
      envVariables:
        PAYMENT_PUBLIC_KEY: ${PAYMENT_PUBLIC_KEY_VAULT}
"""
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_rejects_missing_service_in_import_yaml(self):
        res = self._run_gate(
            """
services:
  - hostname: database
    type: postgresql:single@18
  - hostname: webdev
    type: ubuntu/bun@1.3
    envVariables:
      NATS_URL: ${nats_connectionString}
"""
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("ausente del manifiesto", res.stdout)

    def test_warns_rigid_nats_offline_and_fails_with_check_live_when_absent(self):
        yaml_body = """
zerops:
  - setup: hermes
    run:
      base: ubuntu/python@3.12
      envVariables:
        NATS_URL: ${nats_connectionString}
"""
        res_offline = self._run_gate(yaml_body)
        self.assertEqual(res_offline.returncode, 0, res_offline.stdout + res_offline.stderr)
        self.assertIn("Acoplamiento rígido a NATS", res_offline.stdout)

        res_live = self._run_gate(
            yaml_body,
            extra_args=["--check-live"],
            env_override={"PROJECT_NAME": "demo", "database_hostname": "database"},
        )
        self.assertNotEqual(res_live.returncode, 0)
        self.assertIn("NO existe en el proyecto vivo", res_live.stdout)


if __name__ == "__main__":
    unittest.main()
