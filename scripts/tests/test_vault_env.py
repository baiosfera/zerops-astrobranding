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
    apply_freellmapi_vault,
    build_freellm_declarative_config,
    collect_freellm_pools,
    discover_freellm_pools,
    is_sensitive_vault_key,
    load_pending_freellmapi_seed,
    parse_freellm_markdown,
    parse_kv_file,
    resolve_freellmapi_vault_payload,
    resolve_project_vault_payload,
    split_freellmapi_payload,
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
                        "LINEAR_API_KEY=lin_api_examplevalue123456",
                        "EXA_API_KEY=exa_examplevalue123456",
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
            self.assertNotIn("GITHUB_TOKEN", parsed)
            self.assertNotIn("GITHUB_TOKEN_BAIOSFERA", parsed)
            self.assertNotIn("LINEAR_API_KEY", parsed)
            self.assertNotIn("EXA_API_KEY", parsed)
            self.assertEqual(parsed["AWS_FROM_EMAIL"], "Brand Team <mailer@example.com>")
            self.assertEqual(parsed["DLOCAL_GO_ENV"], "sandbox")
            self.assertNotIn("EMPTY_KEY", parsed)
            self.assertNotIn("ZCP_API_KEY", parsed)
            self.assertEqual(parsed["SMTP_HOST"], "email-smtp.us-east-1.amazonaws.com")
            self.assertEqual(parsed["SMTP_USER"], "AKIAEXAMPLEKEY")

            parsed_op = parse_kv_file(kv_file, include_operator_keys=True)
            self.assertEqual(parsed_op["GITHUB_TOKEN"], "ghp_exampletokenvalue123456")
            self.assertEqual(parsed_op["LINEAR_API_KEY"], "lin_api_examplevalue123456")
            self.assertEqual(parsed_op["EXA_API_KEY"], "exa_examplevalue123456")
            self.assertNotIn("ZCP_API_KEY", parsed_op)

    def test_collect_multi_pool_freellm_and_strict_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "brand_a_freellm.md"
            p2 = Path(tmpdir) / "brand_b_freellm.md"
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
                "cerebras-brand_a",
                "groq-brand_a",
                "openrouter-brand_b",
                "groq-brand_b",
            ])
            self.assertEqual(len(custom_providers), 1)

            cfg = build_freellm_declarative_config(keys_list, custom_providers)
            # Only schema-allowed top-level keys may appear (.strict() on Zod schema).
            self.assertEqual(set(cfg.keys()), {"keys", "models", "fallback", "routing", "customProviders"})
            self.assertEqual(cfg["routing"], {"strategy": "smartest", "keySelectionStrategy": "least-remaining"})
            key_platforms = {k["platform"] for k in cfg["keys"]}
            self.assertIn("kilo", key_platforms)
            self.assertIn("ovh", key_platforms)
            groq_qwen = next(m for m in cfg["models"] if m["platform"] == "groq" and m["modelId"] == "qwen/qwen3.8-27b")
            self.assertFalse(groq_qwen["enabled"])
            groq_safeguard = next(m for m in cfg["models"] if m["platform"] == "groq" and m["modelId"] == "openai/gpt-oss-safeguard-20b")
            self.assertFalse(groq_safeguard["enabled"])
            groq_120b = next(m for m in cfg["models"] if m["platform"] == "groq" and m["modelId"] == "openai/gpt-oss-120b")
            self.assertEqual(groq_120b["tpmLimit"], 8000)
            self.assertGreaterEqual(groq_120b["contextWindow"], 64000)
            json.dumps(cfg)

    def test_sensitivity_classification_and_upsert(self):
        from vault_env import ZcpVaultClient

        # Operational credentials are sensitive by default.
        self.assertTrue(is_sensitive_vault_key("BIFROST_MASTER_VK"))
        self.assertTrue(is_sensitive_vault_key("EVOLUTION_API_KEY"))
        self.assertTrue(is_sensitive_vault_key("PAPERCLIP_ADMIN_PASSWORD"))
        self.assertTrue(is_sensitive_vault_key("TTYD_PASSWORD"))
        self.assertTrue(is_sensitive_vault_key("FREEAPI_ADMIN_PASSWORD"))
        self.assertTrue(is_sensitive_vault_key("FREELLMAPI_CLIENT_KEY"))
        self.assertTrue(is_sensitive_vault_key("DEEPSEEK_API_KEY"))
        self.assertTrue(is_sensitive_vault_key("ASTROLOGY_API_IO"))

        # Usernames/emails and non-secret values stay plain.
        self.assertFalse(is_sensitive_vault_key("EVOLUTION_OPERATOR_EMAIL"))
        self.assertFalse(is_sensitive_vault_key("PAPERCLIP_ADMIN_EMAIL"))
        self.assertFalse(is_sensitive_vault_key("FREEAPI_ADMIN_EMAIL"))
        self.assertFalse(is_sensitive_vault_key("TTYD_USER"))
        self.assertFalse(is_sensitive_vault_key("BIFROST_ADMIN_USER_SECRET"))
        self.assertFalse(is_sensitive_vault_key("PROJECT_NAME"))

        # Opt-in copyable_creds=True exposes only designated operational creds.
        self.assertFalse(is_sensitive_vault_key("BIFROST_MASTER_VK", copyable_creds=True))
        self.assertFalse(is_sensitive_vault_key("TTYD_PASSWORD", copyable_creds=True))
        self.assertTrue(is_sensitive_vault_key("DEEPSEEK_API_KEY", copyable_creds=True))

        calls: list[tuple[str, dict]] = []

        class FakeZcp(ZcpVaultClient):
            def get_project_envs(self):
                return "Demo", {"EXISTING_PLAIN": False, "EXISTING_SECRET": True, "BIFROST_MASTER_VK": True}

            def call_tool(self, name: str, arguments: dict):
                calls.append((name, arguments))
                return {}

        # 1. Default mode: keeps BIFROST_MASTER_VK sensitive, creates new creds as sensitive, filters operator keys.
        summary = FakeZcp().upsert_project_envs(
            {
                "EXISTING_PLAIN": "v1",
                "EXISTING_SECRET": "s1",
                "DEEPSEEK_API_KEY": "sk-ds-123",
                "BIFROST_MASTER_VK": "vk-123",
                "TTYD_PASSWORD": "ttyd-secret-pass",
                "GITHUB_TOKEN": "ghp_should_be_skipped",
                "LINEAR_API_KEY": "lin_should_be_skipped",
                "PROJECT_NAME": "Demo",
            }
        )
        self.assertEqual(summary["existing_sensitive"], 2)
        self.assertEqual(summary["new_sensitive"], 2)
        self.assertEqual(summary["new_plain"], 1)
        self.assertEqual(summary["new_auto"], 3)
        del_calls = [args for _, args in calls if args.get("action") == "delete"]
        self.assertEqual(del_calls, [])
        sens_calls = [args for _, args in calls if args.get("action") == "set" and args.get("sensitive")]
        sens_vars = [v for c in sens_calls for v in c.get("variables", [])]
        self.assertIn("BIFROST_MASTER_VK=vk-123", sens_vars)
        self.assertIn("DEEPSEEK_API_KEY=sk-ds-123", sens_vars)
        self.assertIn("TTYD_PASSWORD=ttyd-secret-pass", sens_vars)
        all_vars = [v for _, args in calls for v in args.get("variables", [])]
        self.assertFalse(any(v.startswith("GITHUB_TOKEN=") or v.startswith("LINEAR_API_KEY=") for v in all_vars))

        # 2. Explicit opt-in copyable_creds=True allows flipping operational creds to plain.
        calls.clear()
        FakeZcp().upsert_project_envs({"BIFROST_MASTER_VK": "vk-123"}, copyable_creds=True)
        del_calls_opt_in = [args for _, args in calls if args.get("action") == "delete"]
        self.assertEqual(len(del_calls_opt_in), 1)
        self.assertEqual(del_calls_opt_in[0]["variables"], ["BIFROST_MASTER_VK"])
        plain_calls_opt_in = [args for _, args in calls if args.get("action") == "set" and not args.get("sensitive")]
        plain_vars_opt_in = [v for c in plain_calls_opt_in for v in c.get("variables", [])]
        self.assertIn("BIFROST_MASTER_VK=vk-123", plain_vars_opt_in)

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

    def test_discover_freellm_pools_isolates_tenants(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            users_apis = Path(tmpdir) / "users-apis"
            users_apis.mkdir()
            global_keys = users_apis / "api_keys_global"
            global_keys.write_text("DEEPSEEK_API_KEY=sk-test\n", encoding="utf-8")
            brand_a = users_apis / "BrandA"
            brand_a.mkdir()
            (brand_a / "branda_freellm.md").write_text("- **Plataforma:** `groq`\n- **API Key:** `gsk_a`\n", encoding="utf-8")
            brand_b = users_apis / "BrandB"
            brand_b.mkdir()
            (brand_b / "brandb_freellm.md").write_text("- **Plataforma:** `groq`\n- **API Key:** `gsk_b`\n", encoding="utf-8")
            brand_c = users_apis / "BrandC"
            brand_c.mkdir()
            brand_c_keys = brand_c / "brandc.md"
            brand_c_keys.write_text("PROJECT_NAME=BrandC\n", encoding="utf-8")

            self.assertEqual(discover_freellm_pools(global_keys), [])
            self.assertEqual(discover_freellm_pools(brand_c_keys), [])
            brand_a_keys = brand_a / "branda.md"
            brand_a_keys.write_text("PROJECT_NAME=BrandA\n", encoding="utf-8")
            self.assertEqual(discover_freellm_pools(brand_a_keys), [str(brand_a / "branda_freellm.md")])

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

    def test_resolve_freellmapi_vault_payload_fresh_and_idempotent_update(self):
        self.assertFalse(is_sensitive_vault_key("FREEAPI_ADMIN_EMAIL"))
        self.assertTrue(is_sensitive_vault_key("FREEAPI_ADMIN_PASSWORD"))
        self.assertFalse(is_sensitive_vault_key("FREEAPI_ADMIN_PASSWORD", copyable_creds=True))

        keys_list = [{"platform": "groq", "key": "dummy_groq_key_1234567890", "label": "groq-test", "enabled": True}]

        # 1. Fresh project seeds credentials matching FREEAPI_CONFIG_JSON_SECRET.
        fresh_cfg, fresh_payload = resolve_freellmapi_vault_payload({}, "Marca Nueva", keys_list, [], existing={})
        self.assertEqual(fresh_payload["FREEAPI_ADMIN_EMAIL"], "freellmapi@marca-nueva.internal")
        self.assertGreaterEqual(len(fresh_payload["FREEAPI_ADMIN_PASSWORD"]), 24)
        self.assertEqual(fresh_cfg["admin"]["email"], fresh_payload["FREEAPI_ADMIN_EMAIL"])
        self.assertEqual(fresh_cfg["admin"]["password"], fresh_payload["FREEAPI_ADMIN_PASSWORD"])
        self.assertEqual(fresh_cfg["unifiedApiKey"], fresh_payload["FREELLMAPI_CLIENT_KEY"])
        self.assertIn("FREEAPI_ENCRYPTION_KEY", fresh_payload)

        # 2. Update on existing project never overwrites existing Vault credentials and reuses plain values.
        existing = {
            "FREEAPI_CONFIG_JSON_SECRET": True,
            "FREEAPI_ENCRYPTION_KEY": True,
            "FREELLMAPI_CLIENT_KEY": False,
            "FREEAPI_ADMIN_EMAIL": False,
            "FREEAPI_ADMIN_PASSWORD": False,
        }
        plain_values = {
            "FREELLMAPI_CLIENT_KEY": "client-key-existing-demo",
            "FREEAPI_ADMIN_EMAIL": "freellmapi@marca-nueva.internal",
            "FREEAPI_ADMIN_PASSWORD": "existing-stable-password",
        }
        upd_cfg, upd_payload = resolve_freellmapi_vault_payload(
            {}, "Marca Nueva", keys_list, [], existing=existing, plain_values=plain_values, rotate=False
        )
        self.assertEqual(set(upd_payload.keys()), {"FREEAPI_CONFIG_JSON_SECRET"})
        self.assertEqual(upd_cfg["unifiedApiKey"], "client-key-existing-demo")
        self.assertEqual(upd_cfg["admin"]["password"], "existing-stable-password")

        # 3. Existing sensitive vault preserves credentials from env_values without rotating.
        sens_existing = {
            "FREEAPI_CONFIG_JSON_SECRET": True,
            "FREEAPI_ENCRYPTION_KEY": True,
            "FREELLMAPI_CLIENT_KEY": True,
            "FREEAPI_ADMIN_EMAIL": False,
            "FREEAPI_ADMIN_PASSWORD": True,
        }
        sens_cfg, sens_payload = resolve_freellmapi_vault_payload(
            {},
            "Marca Sens",
            keys_list,
            [],
            existing=sens_existing,
            plain_values={"FREEAPI_ADMIN_EMAIL": "freellmapi@marca-sens.internal"},
            env_values={
                "FREELLMAPI_CLIENT_KEY": "client-key-env-stable",
                "FREEAPI_ADMIN_PASSWORD": "env-stable-password",
            },
            rotate=False,
        )
        self.assertEqual(set(sens_payload.keys()), {"FREEAPI_CONFIG_JSON_SECRET"})
        self.assertEqual(sens_cfg["unifiedApiKey"], "client-key-env-stable")
        self.assertEqual(sens_cfg["admin"]["password"], "env-stable-password")

        # 4. Existing sensitive vault without plain/env/kv creds never fabricates mismatched random values.
        blind_cfg, blind_payload = resolve_freellmapi_vault_payload(
            {},
            "Marca Blind",
            keys_list,
            [],
            existing=sens_existing,
            plain_values={},
            env_values={},
            rotate=False,
        )
        self.assertEqual(set(blind_payload.keys()), {"FREEAPI_CONFIG_JSON_SECRET"})
        self.assertNotIn("unifiedApiKey", blind_cfg)
        self.assertNotIn("admin", blind_cfg)

        # 5. Legacy vault with FREEAPI_CONFIG_JSON_SECRET but without FREEAPI_ADMIN_PASSWORD does not invent a fake password.
        legacy_existing = {
            "FREEAPI_CONFIG_JSON_SECRET": True,
            "FREEAPI_ENCRYPTION_KEY": True,
            "FREELLMAPI_CLIENT_KEY": False,
        }
        legacy_cfg, legacy_payload = resolve_freellmapi_vault_payload(
            {},
            "Legacy",
            keys_list,
            [],
            existing=legacy_existing,
            plain_values={"FREELLMAPI_CLIENT_KEY": "client-key-legacy-demo"},
            rotate=False,
        )
        self.assertNotIn("FREEAPI_ADMIN_PASSWORD", legacy_payload)
        self.assertNotIn("admin", legacy_cfg)
        self.assertEqual(legacy_cfg["unifiedApiKey"], "client-key-legacy-demo")

        # 6. Explicit --rotate regenerates secrets consistently across Vault and JSON config.
        rot_cfg, rot_payload = resolve_freellmapi_vault_payload(
            {}, "Marca Nueva", keys_list, [], existing=existing, plain_values=plain_values, rotate=True
        )
        self.assertIn("FREEAPI_ADMIN_PASSWORD", rot_payload)
        self.assertNotEqual(rot_payload["FREEAPI_ADMIN_PASSWORD"], "existing-stable-password")
        self.assertEqual(rot_cfg["admin"]["password"], rot_payload["FREEAPI_ADMIN_PASSWORD"])
        self.assertEqual(rot_cfg["unifiedApiKey"], rot_payload["FREELLMAPI_CLIENT_KEY"])

    def test_zcp_vault_client_surfaces_stderr_and_cleans_up_on_auth_failure(self):
        from vault_env import ZcpVaultClient

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_zcp = Path(tmpdir) / "zcp"
            fake_zcp.write_text(
                "#!/bin/sh\necho '2026/11/24 12:16:14 auth: Not authorized' >&2\nexit 1\n",
                encoding="utf-8",
            )
            fake_zcp.chmod(0o755)
            client = ZcpVaultClient(zcp_bin=str(fake_zcp))
            with self.assertRaises(RuntimeError) as ctx:
                with client:
                    pass
            msg = str(ctx.exception)
            self.assertIn("auth: Not authorized", msg)
            self.assertIn("ZCP_API_KEY", msg)
            self.assertIsNone(client._proc)

    def test_project_vault_blocks_oversized_and_service_only_keys(self):
        from vault_env import ZcpVaultClient

        calls: list[tuple[str, dict]] = []

        class FakeZcp(ZcpVaultClient):
            def get_project_envs(self):
                return "Demo", {}

            def call_tool(self, name: str, arguments: dict):
                calls.append((name, arguments))
                return {}

        summary = FakeZcp().upsert_project_envs(
            {
                "FREEAPI_CONFIG_JSON_SECRET": '{"keys":[]}',
                "FREEAPI_ENCRYPTION_KEY": "a" * 64,
                "HUGE_BLOB": "x" * 3000,
                "FREELLMAPI_CLIENT_KEY": "client-key-demo-1234567890",
            }
        )
        self.assertEqual(summary["new_sensitive"], 1)
        all_vars = [v for _, args in calls for v in args.get("variables", [])]
        self.assertEqual(all_vars, ["FREELLMAPI_CLIENT_KEY=client-key-demo-1234567890"])

    def test_apply_freellmapi_vault_defers_when_absent_and_targets_service_when_present(self):
        from vault_env import ZcpVaultClient

        keys_list = [{"platform": "groq", "key": "dummy_groq_key_1234567890", "label": "groq-test", "enabled": True}]

        class FakeStatefulZcp(ZcpVaultClient):
            def __init__(self, has_freellmapi: bool):
                super().__init__()
                self.has_freellmapi = has_freellmapi
                self.proj_envs: dict[str, tuple[str, bool]] = {"FREEAPI_CONFIG_JSON_SECRET": ("old", True)}
                self.svc_envs: dict[str, tuple[str, bool]] = {}

            def list_services(self):
                return {"zcp", "freellmapi"} if self.has_freellmapi else {"zcp"}

            def get_project_envs(self):
                return "Demo", {k: sens for k, (_, sens) in self.proj_envs.items()}

            def get_service_envs(self, service_hostname: str):
                assert service_hostname == "freellmapi"
                return {k: sens for k, (_, sens) in self.svc_envs.items()}

            def get_project_plain_env_values(self):
                return {k: val for k, (val, sens) in self.proj_envs.items() if not sens}

            def call_tool(self, name: str, arguments: dict):
                assert name == "zerops_env"
                target = self.proj_envs if arguments.get("project") else self.svc_envs
                action = arguments["action"]
                if action == "delete":
                    for k in arguments.get("variables", []):
                        target.pop(k, None)
                elif action == "set":
                    sens = bool(arguments.get("sensitive", False))
                    for pair in arguments.get("variables", []):
                        k, v = pair.split("=", 1)
                        target[k] = (v, sens)
                return {}

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "freellmapi-seed.json"
            fake = FakeStatefulZcp(has_freellmapi=False)

            # 1. Before freellmapi exists: never puts FREEAPI_CONFIG_JSON_SECRET in project vault, cleans legacy leak, stages non-secret pointer.
            res_deferred = apply_freellmapi_vault(
                fake,
                {},
                "Demo",
                keys_list,
                [],
                env_values={},
                keys_file="/tmp/keys.md",
                pools=["/tmp/pool_freellm.md"],
                state_path=state_file,
            )
            self.assertEqual(res_deferred["mode"], "deferred_until_freellmapi_created")
            self.assertNotIn("FREEAPI_CONFIG_JSON_SECRET", fake.proj_envs)
            self.assertIn("FREELLMAPI_CLIENT_KEY", fake.proj_envs)
            self.assertEqual(fake.svc_envs, {})
            staged = load_pending_freellmapi_seed(state_file)
            self.assertIsNotNone(staged)
            self.assertEqual(staged["keys_file"], "/tmp/keys.md")
            self.assertNotIn("dummy_groq_key", state_file.read_text(encoding="utf-8"))

            # 2. Once freellmapi exists: writes config & encryption key directly to freellmapi (sensitive=True) and clears pointer.
            fake.has_freellmapi = True
            fake.proj_envs["FREEAPI_CONFIG_JSON_SECRET"] = ("stale", True)
            res_svc = apply_freellmapi_vault(
                fake,
                {},
                "Demo",
                keys_list,
                [],
                env_values={},
                keys_file="/tmp/keys.md",
                pools=["/tmp/pool_freellm.md"],
                state_path=state_file,
            )
            self.assertEqual(res_svc["mode"], "service")
            self.assertNotIn("FREEAPI_CONFIG_JSON_SECRET", fake.proj_envs)
            self.assertNotIn("FREEAPI_ENCRYPTION_KEY", fake.proj_envs)
            self.assertTrue(fake.svc_envs["FREEAPI_CONFIG_JSON_SECRET"][1])
            self.assertTrue(fake.svc_envs["FREEAPI_ENCRYPTION_KEY"][1])
            self.assertIsNone(load_pending_freellmapi_seed(state_file))
            svc_p, sh_p = split_freellmapi_payload({"FREEAPI_CONFIG_JSON_SECRET": "x", "FREELLMAPI_CLIENT_KEY": "y"})
            self.assertEqual(set(svc_p.keys()), {"FREEAPI_CONFIG_JSON_SECRET"})
            self.assertEqual(set(sh_p.keys()), {"FREELLMAPI_CLIENT_KEY"})


if __name__ == "__main__":
    unittest.main()
