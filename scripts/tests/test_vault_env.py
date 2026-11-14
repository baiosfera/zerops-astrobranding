"""Unit tests for shared Vault parsing and multi-pool FreeLLMAPI config generation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from vault_env import (
    build_freellm_declarative_config,
    collect_freellm_pools,
    discover_freellm_pools,
    is_sensitive_vault_key,
    parse_freellm_markdown,
    parse_kv_file,
    resolve_project_vault_payload,
)


class TestVaultEnv(unittest.TestCase):
    """Verify `.md` / `.env` key parsing and strict FreeLLMAPI config building."""

    def test_parse_kv_file_strips_comments_preserves_angles_and_filters_zcp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            kv_file = Path(tmpdir) / "brand.md"
            kv_file.write_text(
                "\n".join(
                    [
                        "# Brand Secrets",
                        "GITHUB_TOKEN_BAIOSFERA=ghp_exampletokenvalue123456",
                        "AWS_FROM_EMAIL=Brand Team <mailer@example.com>",
                        "DLOCAL_GO_ENV=sandbox # comment outside quotes",
                        "EMPTY_KEY=",
                        "ZCP_API_KEY=zcp_must_never_enter_shared_vault",
                        "AWS_ACCESS_KEY_ID=AKIAEXAMPLEKEY",
                        "AWS_SECRET_ACCESS_KEY=secretvalue123",
                    ]
                ),
                encoding="utf-8",
            )
            parsed = parse_kv_file(kv_file)
            self.assertEqual(parsed["GITHUB_TOKEN"], "ghp_exampletokenvalue123456")
            self.assertEqual(parsed["AWS_FROM_EMAIL"], "Brand Team <mailer@example.com>")
            self.assertEqual(parsed["DLOCAL_GO_ENV"], "sandbox")
            self.assertNotIn("EMPTY_KEY", parsed)
            self.assertNotIn("ZCP_API_KEY", parsed)
            self.assertEqual(parsed["SMTP_HOST"], "email-smtp.us-east-1.amazonaws.com")
            self.assertEqual(parsed["SMTP_USER"], "AKIAEXAMPLEKEY")

    def test_collect_multi_pool_freellm_and_strict_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "baiosfera_freellm.md"
            p2 = Path(tmpdir) / "damaren_freellm.md"
            p1.write_text(
                "- **Plataforma:** `cerebras`\n- **API Key:** `csk-acc1`\n"
                "- **Plataforma:** `groq`\n- **API Key:** `gsk_acc1`\n",
                encoding="utf-8",
            )
            p2.write_text(
                "- **Plataforma:** `openrouter`\n- **API Key:** `sk-or-acc2`\n"
                "- **Plataforma:** `groq`\n- **API Key:** `gsk_acc2`\n"
                "- **Plataforma:** `aisa`\n- **API Key:** `aisa-acc2`\n",
                encoding="utf-8",
            )
            self.assertEqual(len(parse_freellm_markdown(p1)), 2)
            keys_list, custom_providers, sources = collect_freellm_pools([str(p1), str(p2)])
            self.assertEqual(len(sources), 2)
            self.assertEqual([k["label"] for k in keys_list], [
                "cerebras-baiosfera",
                "groq-baiosfera",
                "openrouter-damaren",
                "groq-damaren",
            ])
            self.assertEqual(len(custom_providers), 1)

            cfg = build_freellm_declarative_config(keys_list, custom_providers)
            # Only schema-allowed top-level keys may appear (.strict() on Zod schema).
            self.assertEqual(set(cfg.keys()), {"keys", "models", "fallback", "routing", "customProviders"})
            self.assertEqual(cfg["routing"], {"strategy": "smartest", "keySelectionStrategy": "least-remaining"})
            groq_qwen = next(m for m in cfg["models"] if m["platform"] == "groq" and m["modelId"] == "qwen/qwen3.8-27b")
            self.assertEqual(groq_qwen["tpmLimit"], 7000)
            json.dumps(cfg)

    def test_sensitivity_classification_and_upsert(self):
        from vault_env import ZcpVaultClient

        self.assertFalse(is_sensitive_vault_key("BIFROST_MASTER_VK"))
        self.assertFalse(is_sensitive_vault_key("EVOLUTION_API_KEY"))
        self.assertFalse(is_sensitive_vault_key("EVOLUTION_OPERATOR_EMAIL"))
        self.assertFalse(is_sensitive_vault_key("PAPERCLIP_ADMIN_PASSWORD"))
        self.assertFalse(is_sensitive_vault_key("TTYD_PASSWORD"))
        self.assertTrue(is_sensitive_vault_key("DEEPSEEK_API_KEY"))
        self.assertTrue(is_sensitive_vault_key("ASTROLOGY_API_IO"))
        self.assertFalse(is_sensitive_vault_key("PROJECT_NAME"))

        calls: list[tuple[str, dict]] = []

        class FakeZcp(ZcpVaultClient):
            def get_project_envs(self):
                return "Demo", {"EXISTING_PLAIN": False, "EXISTING_SECRET": True, "BIFROST_MASTER_VK": True}

            def call_tool(self, name: str, arguments: dict):
                calls.append((name, arguments))
                return {}

        summary = FakeZcp().upsert_project_envs(
            {
                "EXISTING_PLAIN": "v1",
                "EXISTING_SECRET": "s1",
                "DEEPSEEK_API_KEY": "sk-ds-123",
                "BIFROST_MASTER_VK": "vk-123",
                "PROJECT_NAME": "Demo",
            }
        )
        self.assertEqual(summary["new_sensitive"], 1)
        self.assertEqual(summary["new_plain"], 2)
        self.assertEqual(summary["new_auto"], 3)
        sens_calls = [args for _, args in calls if args.get("variables") == ["DEEPSEEK_API_KEY=sk-ds-123"]]
        self.assertEqual(len(sens_calls), 1)
        self.assertTrue(sens_calls[0]["sensitive"])
        plain_calls = [args for _, args in calls if args.get("action") == "set" and not args.get("sensitive")]
        plain_vars = [v for c in plain_calls for v in c.get("variables", [])]
        self.assertIn("BIFROST_MASTER_VK=vk-123", plain_vars)
        del_calls = [args for _, args in calls if args.get("action") == "delete"]
        self.assertEqual(len(del_calls), 1)
        self.assertEqual(del_calls[0]["variables"], ["BIFROST_MASTER_VK"])

    def test_discover_freellm_pools_from_keys_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            brand_dir = root / "MarcaX"
            brand_dir.mkdir()
            keys_file = brand_dir / "marcax.md"
            keys_file.write_text("PROJECT_NAME=MarcaX\n", encoding="utf-8")
            sibling_pool = brand_dir / "marcax_freellm.md"
            sibling_pool.write_text("GROQ_API_KEY=gsk_test12345678901234567890\n", encoding="utf-8")
            extra_pool = root / "extra_freellm.md"
            extra_pool.write_text("CEREBRAS_API_KEY=csk_test12345678901234567890\n", encoding="utf-8")

            discovered = discover_freellm_pools(keys_file, [str(extra_pool), str(sibling_pool)])
            self.assertEqual(discovered, [str(extra_pool), str(sibling_pool)])
            self.assertEqual(len(discovered), len(set(discovered)))

    def test_resolve_project_vault_payload_is_independent(self):
        payload = resolve_project_vault_payload(
            {
                "DEEPSEEK_API_KEY": "sk-ds-demo",
                "EVOLUTION_OPERATOR_EMAIL": "ops@marcax.com",
                "FREEAPI_ADMIN_EMAIL": "legacy-free@marcax.com",
                "FREEAPI_ADMIN_PASSWORD": "legacy-free-password",
            },
            "Marca X",
            existing={},
            rotate=False,
        )
        self.assertEqual(payload["PROJECT_NAME"], "Marca X")
        self.assertEqual(payload["ENGRAM_PROJECT"], "Marca X")
        self.assertEqual(payload["PAPERCLIP_ADMIN_EMAIL"], "paperclip@marca-x.internal")
        self.assertNotIn("FREEAPI_ADMIN_EMAIL", payload)
        self.assertNotIn("FREEAPI_ADMIN_PASSWORD", payload)
        self.assertNotEqual(payload["PAPERCLIP_ADMIN_PASSWORD"], "legacy-free-password")
        self.assertEqual(payload["EVOLUTION_OPERATOR_EMAIL"], "ops@marcax.com")
        self.assertEqual(payload["DEEPSEEK_API_KEY"], "sk-ds-demo")
        self.assertTrue(payload["BIFROST_MASTER_VK"].startswith("vk-bifrost-"))
        self.assertTrue(payload["EVOLUTION_API_KEY"].startswith("evo-"))

    def test_build_freellm_declarative_config_admin_and_unified_key(self):
        cfg = build_freellm_declarative_config(
            [{"provider": "groq", "label": "acct-1", "key": "gsk_12345678901234567890"}],
            [],
            admin_email="freellmapi@marca-x.internal",
            admin_password="super-secret-password",
            unified_api_key="sk-freellmapi-testkey",
        )
        self.assertEqual(
            cfg["admin"],
            {"email": "freellmapi@marca-x.internal", "password": "super-secret-password"},
        )
        self.assertEqual(cfg["unifiedApiKey"], "sk-freellmapi-testkey")


if __name__ == "__main__":
    unittest.main()
