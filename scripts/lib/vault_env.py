"""Shared Zerops Project Vault and FreeLLMAPI configuration utilities.

Provides idempotent key-file parsing (`.env` / `.md`), multi-account FreeLLMAPI
pool compilation (`baiosfera_freellm.md` + `damaren_freellm.md`), and masked
JSON-RPC synchronization with Zerops Shared Vault (`zerops_env project=true`).
Never prints secret values to stdout/stderr.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import string
import subprocess
from pathlib import Path
from typing import Any, Optional

DEFAULT_ZCP_BIN = "/usr/local/bin/zcp"
DEFAULT_FREELLM_POOLS = (
    "/var/www/baiosfera/0ZEROPS-AGY/users-apis/Baiosfera/baiosfera_freellm.md",
    "/var/www/baiosfera/0ZEROPS-AGY/users-apis/Damaren/damaren_freellm.md",
)

# Host-local or platform-private keys that must never be pushed to Project Shared Vault.
IGNORED_VAULT_KEYS = re.compile(
    r"^(PATH|PWD|OLDPWD|HOME|USER|LOGNAME|SHELL|SHLVL|_|LS_COLORS|"
    r"DEBIAN_FRONTEND|TERM|HOSTNAME|LANG|LC_.*|SSH_.*|MAIL|HIST.*|LESS.*|"
    r"ZCP_API_KEY|ZEROPS_TOKEN|Z_TOKEN|ZEROPS_API_KEY|INICIAR_REEXEC)$"
)

# Suffixes and explicit credential names that must always be stored as sensitive when created.
SENSITIVE_VAULT_KEYS = re.compile(
    r"(SECRET|TOKEN|KEY|PASSWORD|PASS|DSN|PRIVATE|CREDENTIAL|_VK$|_PAT$|^ASTROLOGY_API_IO$)",
    re.IGNORECASE,
)


def is_sensitive_vault_key(key: str) -> bool:
    """Return True when a vault variable name holds a secret or virtual key."""
    return bool(SENSITIVE_VAULT_KEYS.search(key))

_FREELLM_KEY_PLATFORMS = ("cerebras", "groq", "ollama", "openrouter", "opencode", "huggingface", "mistral", "google", "cohere", "nvidia")

# Curated catalog models aligned with live catalog v2026.11+: throttle Groq qwen3.8-27b to 7,000 TPM
# and disable small guard models from chat/code routing while prioritizing strong reasoning/coding models.
_CURATED_MODELS: list[dict[str, Any]] = [
    {"platform": "groq", "modelId": "qwen/qwen3.8-27b", "tpmLimit": 7000, "enabled": True, "fallbackEnabled": True},
    {"platform": "groq", "modelId": "allam-2-7b", "enabled": False, "fallbackEnabled": False},
    {"platform": "groq", "modelId": "meta-llama/llama-prompt-guard-2-22m", "enabled": False, "fallbackEnabled": False},
    {"platform": "groq", "modelId": "meta-llama/llama-prompt-guard-2-86m", "enabled": False, "fallbackEnabled": False},
    {"platform": "cerebras", "modelId": "qwen-3.8-27b", "enabled": True, "fallbackEnabled": True},
    {"platform": "openrouter", "modelId": "nvidia/nemotron-3.5-lightning:free", "enabled": True, "fallbackEnabled": True},
    {"platform": "openrouter", "modelId": "nvidia/nemotron-3.5-super-vl:free", "enabled": True, "fallbackEnabled": True},
    {"platform": "openrouter", "modelId": "dots-studio/dots-3-note-preview:free", "enabled": True, "fallbackEnabled": True},
    {"platform": "openrouter", "modelId": "openrouter/free", "enabled": True, "fallbackEnabled": True},
    {"platform": "openrouter", "modelId": "google/gemma-4-31b-it:free", "enabled": True, "fallbackEnabled": True},
    {"platform": "openrouter", "modelId": "cohere/north-mini-code:free", "enabled": True, "fallbackEnabled": True},
    {"platform": "ollama", "modelId": "nemotron-3-super", "enabled": True, "fallbackEnabled": True},
    {"platform": "ollama", "modelId": "gemma4:31b", "enabled": True, "fallbackEnabled": True},
    {"platform": "ollama", "modelId": "nemotron-3-ultra", "enabled": True, "fallbackEnabled": True},
    {"platform": "ollama", "modelId": "beam", "enabled": True, "fallbackEnabled": True},
]

_CURATED_FALLBACK: list[dict[str, Any]] = [
    {"platform": "cerebras", "modelId": "qwen-3.8-27b", "priority": 1, "enabled": True},
    {"platform": "groq", "modelId": "qwen/qwen3.8-27b", "priority": 2, "enabled": True},
    {"platform": "openrouter", "modelId": "nvidia/nemotron-3.5-lightning:free", "priority": 3, "enabled": True},
    {"platform": "openrouter", "modelId": "nvidia/nemotron-3.5-super-vl:free", "priority": 4, "enabled": True},
    {"platform": "openrouter", "modelId": "dots-studio/dots-3-note-preview:free", "priority": 5, "enabled": True},
    {"platform": "openrouter", "modelId": "openrouter/free", "priority": 6, "enabled": True},
    {"platform": "openrouter", "modelId": "google/gemma-4-31b-it:free", "priority": 7, "enabled": True},
    {"platform": "openrouter", "modelId": "cohere/north-mini-code:free", "priority": 8, "enabled": True},
    {"platform": "ollama", "modelId": "nemotron-3-super", "priority": 9, "enabled": True},
    {"platform": "ollama", "modelId": "gemma4:31b", "priority": 10, "enabled": True},
    {"platform": "ollama", "modelId": "nemotron-3-ultra", "priority": 11, "enabled": True},
    {"platform": "ollama", "modelId": "beam", "priority": 12, "enabled": True},
]


def _unquote_and_strip(raw_val: str) -> str:
    """Clean outer quotes and strip inline `# comments` only when unquoted."""
    v = raw_val.strip().rstrip("\r")
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1].strip()
    if " #" in v:
        v = v.split(" #", 1)[0].strip()
    elif v.startswith("#"):
        return ""
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        v = v[1:-1].strip()
    return v


def parse_kv_file(path: str | Path, *, apply_derivations: bool = True, filter_vault_ignored: bool = True) -> dict[str, str]:
    """Parse `.env` or `.md` secret files into a clean key->value dictionary."""
    file_path = Path(path)
    if not file_path.is_file():
        return {}

    raw_keys: dict[str, str] = {}
    pending_key: Optional[str] = None
    in_code_fence = False

    with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line.startswith("```"):
                in_code_fence = not in_code_fence
                continue
            if not line or line.startswith("#"):
                continue

            candidate = line[7:].strip() if line.startswith("export ") else line
            kv_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", candidate)
            if kv_match:
                k, raw_v = kv_match.group(1), kv_match.group(2)
                v = _unquote_and_strip(raw_v)
                if v:
                    raw_keys[k] = v
                pending_key = None
                continue

            if ":" in line and not line.startswith("http") and not in_code_fence:
                left, _, right = line.partition(":")
                left_clean = left.strip().lstrip("-* ").strip("*` ")
                if left_clean.isidentifier():
                    v = _unquote_and_strip(right.strip().strip("`"))
                    if v:
                        raw_keys[left_clean] = v
                    pending_key = None
                    continue

            if line.isidentifier():
                pending_key = line
            elif pending_key:
                v = _unquote_and_strip(line)
                if v:
                    raw_keys[pending_key] = v
                pending_key = None

    synonyms = {
        "FIRE_CRAWL_API": "FIRECRAWL_API_KEY",
        "FIRE_CRAWL_API_KEY": "FIRECRAWL_API_KEY",
        "GITHUB_API_KEY": "GITHUB_TOKEN",
        "GITHUB_TOKEN_BAIOSFERA": "GITHUB_TOKEN",
        "ASTRO_WAY_API": "ASTROWAY_API_KEY",
        "ASTRO_API_KEY": "VEDASTRO_API_KEY",
    }
    for src_k, dst_k in synonyms.items():
        if src_k in raw_keys and dst_k not in raw_keys:
            raw_keys[dst_k] = raw_keys[src_k]

    if apply_derivations:
        if raw_keys.get("AWS_ACCESS_KEY_ID") and raw_keys.get("AWS_SECRET_ACCESS_KEY"):
            raw_keys.setdefault("AWS_REGION", "us-east-1")
            raw_keys.setdefault("SMTP_HOST", f"email-smtp.{raw_keys['AWS_REGION']}.amazonaws.com")
            raw_keys.setdefault("SMTP_PORT", "587")
            raw_keys.setdefault("SMTP_USER", raw_keys["AWS_ACCESS_KEY_ID"])
            raw_keys.setdefault("SMTP_PASSWORD", raw_keys["AWS_SECRET_ACCESS_KEY"])
        if raw_keys.get("ZEPTOMAIL_SEND_MAIL_TOKEN"):
            raw_keys.setdefault("SMTP_HOST", "smtp.zeptomail.com")
            raw_keys.setdefault("SMTP_PORT", "587")
            raw_keys.setdefault("SMTP_USER", "emailapikey")
            raw_keys.setdefault("SMTP_PASSWORD", raw_keys["ZEPTOMAIL_SEND_MAIL_TOKEN"])

    if filter_vault_ignored:
        raw_keys = {k: v for k, v in raw_keys.items() if not IGNORED_VAULT_KEYS.match(k)}

    return raw_keys


def _account_tag_from_path(path: Path) -> str:
    stem = path.stem.lower()
    for suffix in ("_freellm", "-freellm", "_keys", "-keys"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return re.sub(r"[^a-z0-9_-]+", "-", stem).strip("-") or "pool"


def parse_freellm_markdown(filepath: str | Path) -> list[tuple[str, str, str]]:
    """Parse `- **Plataforma:**` and `- **API Key:**` blocks from a FreeLLM markdown pool."""
    path = Path(filepath)
    if not path.is_file():
        return []
    tag = _account_tag_from_path(path)
    entries: list[tuple[str, str, str]] = []
    current_platform: Optional[str] = None
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            plat_m = re.search(r"\*\*Plataforma:\*\*\s*`([^`]+)`", line)
            if plat_m:
                current_platform = plat_m.group(1).strip().lower()
                continue
            key_m = re.search(r"\*\*API Key:\*\*\s*`([^`]+)`", line)
            if key_m and current_platform:
                key_val = key_m.group(1).strip()
                if key_val:
                    entries.append((current_platform, key_val, tag))
                current_platform = None
    return entries


def collect_freellm_pools(
    pool_paths: list[str] | tuple[str, ...] = DEFAULT_FREELLM_POOLS,
    extra_kv: Optional[dict[str, str]] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Aggregate multiple primary FreeLLM accounts without duplicating `(platform, key)` pairs."""
    keys_list: list[dict[str, Any]] = []
    custom_providers: list[dict[str, Any]] = []
    loaded_sources: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    seen_custom_keys: set[str] = set()

    for pool_str in pool_paths:
        p = Path(pool_str)
        if not p.is_file():
            continue
        parsed = parse_freellm_markdown(p)
        if not parsed:
            continue
        loaded_sources.append(str(p))
        for plat, key_val, tag in parsed:
            if plat == "aisa":
                if key_val not in seen_custom_keys:
                    seen_custom_keys.add(key_val)
                    custom_providers.append(
                        {
                            "baseUrl": "https://api.aisa.one/v1",
                            "apiKey": key_val,
                            "label": f"Aisa One ({tag})",
                            "models": [{"model": "gpt-4o-mini", "displayName": "Aisa GPT-4o Mini", "supportsTools": True}],
                        }
                    )
                continue
            pair = (plat, key_val)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            keys_list.append({"platform": plat, "key": key_val, "label": f"{plat}-{tag}", "enabled": True})

    if extra_kv:
        for plat in _FREELLM_KEY_PLATFORMS:
            val = extra_kv.get(f"{plat.upper()}_API_KEY", "").strip()
            if val and (plat, val) not in seen_pairs:
                seen_pairs.add((plat, val))
                keys_list.append({"platform": plat, "key": val, "label": f"{plat}-vault", "enabled": True})
        aisa_val = extra_kv.get("AISA_API_KEY", "").strip()
        if aisa_val and aisa_val not in seen_custom_keys:
            custom_providers.append(
                {
                    "baseUrl": "https://api.aisa.one/v1",
                    "apiKey": aisa_val,
                    "label": "Aisa One (vault)",
                    "models": [{"model": "gpt-4o-mini", "displayName": "Aisa GPT-4o Mini", "supportsTools": True}],
                }
            )

    return keys_list, custom_providers, loaded_sources


def build_freellm_declarative_config(
    keys_list: list[dict[str, Any]],
    custom_providers: list[dict[str, Any]],
    *,
    admin_email: Optional[str] = None,
    admin_password: Optional[str] = None,
    unified_api_key: Optional[str] = None,
) -> dict[str, Any]:
    """Build strict schema-compliant JSON for FreeLLMAPI `FREEAPI_CONFIG_JSON`."""
    cfg: dict[str, Any] = {
        "keys": keys_list,
        "models": _CURATED_MODELS,
        "fallback": _CURATED_FALLBACK,
        "routing": {"strategy": "smartest", "keySelectionStrategy": "least-remaining"},
    }
    if admin_email and admin_password and len(admin_password) >= 8:
        cfg["admin"] = {"email": admin_email, "password": admin_password}
    if unified_api_key and len(unified_api_key) >= 8:
        cfg["unifiedApiKey"] = unified_api_key
    if custom_providers:
        cfg["customProviders"] = custom_providers
    return cfg


def generate_secret(length: int = 32, *, hex_only: bool = False) -> str:
    """Generate a cryptographically secure random secret or 64-char hex encryption key."""
    if hex_only:
        return secrets.token_hex(length)
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class ZcpVaultClient:
    """Minimal JSON-RPC client talking directly to `/usr/local/bin/zcp serve`."""

    def __init__(self, zcp_bin: str = DEFAULT_ZCP_BIN) -> None:
        self.zcp_bin = zcp_bin
        self._proc: Optional[subprocess.Popen[str]] = None
        self._next_id = 1

    def __enter__(self) -> "ZcpVaultClient":
        if not os.path.exists(self.zcp_bin):
            raise FileNotFoundError(f"zcp binary not found at {self.zcp_bin}")
        self._proc = subprocess.Popen(
            [self.zcp_bin, "serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "zerops-astrobranding-vault", "version": "3.0"},
            },
        )
        assert self._proc.stdin is not None
        self._proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self._proc.stdin.flush()
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()
            self._proc = None

    def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        assert self._proc is not None and self._proc.stdin is not None and self._proc.stdout is not None
        req_id = self._next_id
        self._next_id += 1
        self._proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n")
        self._proc.stdin.flush()
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("zcp serve closed stdout unexpectedly")
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if data.get("id") == req_id:
                if "error" in data:
                    raise RuntimeError(f"zcp JSON-RPC error: {data['error']}")
                return data

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        resp = self._rpc("tools/call", {"name": name, "arguments": arguments})
        result = resp.get("result", {})
        if result.get("isError"):
            text = (result.get("content") or [{}])[0].get("text", "unknown tool error")
            raise RuntimeError(f"zcp tool {name} failed: {text}")
        raw_text = (result.get("content") or [{}])[0].get("text", "{}")
        return json.loads(raw_text) if raw_text.strip().startswith("{") else {"raw": raw_text}

    def get_project_envs(self) -> tuple[str, dict[str, bool]]:
        """Return `(project_name, {key: isSensitive})` without reading sensitive values."""
        data = self.call_tool("zerops_env", {"action": "get", "project": True})
        project_name = str(data.get("project", {}).get("name") or "").strip()
        existing = {
            str(entry["key"]): bool(entry.get("isSensitive", False))
            for entry in data.get("envs", [])
            if entry.get("key")
        }
        return project_name, existing

    def upsert_project_envs(self, kv: dict[str, str], *, skip_restart: bool = True) -> dict[str, int]:
        """Upsert variables into Project Shared Vault respecting existing sensitivity groups."""
        if not kv:
            return {"existing_sensitive": 0, "existing_plain": 0, "new_auto": 0, "new_sensitive": 0, "new_plain": 0}
        _, existing = self.get_project_envs()

        existing_sensitive: list[str] = []
        existing_plain: list[str] = []
        new_sensitive: list[str] = []
        new_plain: list[str] = []

        for k in sorted(kv):
            v = kv[k]
            if not v or IGNORED_VAULT_KEYS.match(k):
                continue
            pair = f"{k}={v}"
            if k in existing:
                (existing_sensitive if existing[k] else existing_plain).append(pair)
            elif is_sensitive_vault_key(k):
                new_sensitive.append(pair)
            else:
                new_plain.append(pair)

        if existing_sensitive:
            self.call_tool(
                "zerops_env",
                {"action": "set", "project": True, "sensitive": True, "skipRestart": skip_restart, "variables": existing_sensitive},
            )
        if existing_plain:
            self.call_tool(
                "zerops_env",
                {"action": "set", "project": True, "sensitive": False, "skipRestart": skip_restart, "variables": existing_plain},
            )
        if new_sensitive:
            self.call_tool(
                "zerops_env",
                {"action": "set", "project": True, "sensitive": True, "skipRestart": skip_restart, "variables": new_sensitive},
            )
        if new_plain:
            self.call_tool(
                "zerops_env",
                {"action": "set", "project": True, "sensitive": False, "skipRestart": skip_restart, "variables": new_plain},
            )

        return {
            "existing_sensitive": len(existing_sensitive),
            "existing_plain": len(existing_plain),
            "new_auto": len(new_sensitive) + len(new_plain),
            "new_sensitive": len(new_sensitive),
            "new_plain": len(new_plain),
        }
