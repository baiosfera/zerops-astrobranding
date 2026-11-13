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
    parse_freellm_markdown,
    parse_kv_file,
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


if __name__ == "__main__":
    unittest.main()
