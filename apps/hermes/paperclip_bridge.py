"""
Paperclip Bidirectional Telemetry & Task Bridge for Hermes Agent.
Synchronizes Telegram conversation turns, tool actions, and heartbeat runs
directly into Paperclip Control Plane (PostgreSQL 18 + Activity Stream).
"""
import os
import json
import uuid
import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("hermes.paperclip_bridge")

# Default UUIDs for Baiosfera in Paperclip SSoT
DEFAULT_COMPANY_ID = "2c915432-4c84-4b01-b90b-ee7482147eef"
DEFAULT_HERMES_AGENT_ID = "22222222-2222-2222-2222-222222222222"
DEFAULT_RESPONSIBLE_USER_ID = "xy80KZka8U4baAQBJwmSzEVOFjd2GRby"

_DB_CONN_STR: Optional[str] = None

def get_paperclip_db_url() -> Optional[str]:
    """
    Dynamically discovers the canonical PostgreSQL connection string
    from Paperclip instance config or environment without hardcoded secrets.
    """
    global _DB_CONN_STR
    if _DB_CONN_STR:
        return _DB_CONN_STR

    # 1. Direct environment override
    env_url = os.getenv("PAPERCLIP_DATABASE_URL")
    if env_url:
        _DB_CONN_STR = env_url
        return _DB_CONN_STR

    # 2. LocalStorage NVMe instance config
    for candidate_path in [
        "/mnt/localstorage/paperclip/instances/default/config.json",
        "/var/www/localstorage/paperclip/instances/default/config.json",
        os.path.expanduser("~/.paperclip/instances/default/config.json"),
    ]:
        if os.path.exists(candidate_path):
            try:
                with open(candidate_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    db_str = cfg.get("database", {}).get("connectionString")
                    if db_str:
                        _DB_CONN_STR = db_str
                        return _DB_CONN_STR
            except Exception as e:
                logger.warning("Could not read Paperclip config from %s: %s", candidate_path, e)

    # 3. Fallback to DATABASE_URL if pointing to paperclip database
    fallback = os.getenv("DATABASE_URL", "")
    if "paperclip" in fallback:
        _DB_CONN_STR = fallback
        return _DB_CONN_STR

    return None

async def record_telegram_turn(
    user_id: Any,
    prompt: str,
    reply: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_cents: int = 0,
    duration_sec: float = 0.0,
    company_id: str = DEFAULT_COMPANY_ID,
    agent_id: str = DEFAULT_HERMES_AGENT_ID,
) -> bool:
    """
    Records a completed Telegram conversation turn into Paperclip Control Plane:
    1. Creates a completed record in heartbeat_runs with token & cost telemetry.
    2. Emits an audit event in activity_log for real-time dashboard visibility.
    3. Updates agent last_heartbeat_at timestamp and active status.
    Fully fail-safe: failures are logged without blocking conversational flow.
    """
    db_url = get_paperclip_db_url()
    if not db_url:
        logger.debug("Paperclip database URL not available; skipping telemetry sync.")
        return False

    try:
        import asyncpg
    except ImportError:
        logger.warning("asyncpg module not available in Hermes environment.")
        return False

    # Estimate token counts if not provided (~4 chars per token standard)
    if tokens_in <= 0 and prompt:
        tokens_in = max(1, len(prompt) // 4)
    if tokens_out <= 0 and reply:
        tokens_out = max(1, len(reply) // 4)

    run_id = uuid.uuid4()
    company_uuid = uuid.UUID(company_id)
    agent_uuid = uuid.UUID(agent_id)

    usage_payload = json.dumps({
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "cost_cents": cost_cents,
        "duration_sec": round(duration_sec, 2),
    })

    summary_text = (reply[:197] + "...") if len(reply) > 200 else reply
    result_payload = json.dumps({"summary": summary_text})

    activity_details = json.dumps({
        "channel": "telegram",
        "user_id": str(user_id),
        "prompt": prompt[:300] if prompt else "",
        "reply": summary_text,
        "tokens": {"input": tokens_in, "output": tokens_out},
        "duration_sec": round(duration_sec, 2),
    })

    conn = None
    try:
        conn = await asyncpg.connect(db_url, timeout=5.0)

        # 1. Insert heartbeat run
        await conn.execute(
            """
            INSERT INTO heartbeat_runs (
                id, company_id, agent_id, invocation_source, status, trigger_detail,
                started_at, finished_at, stdout_excerpt, usage_json, result_json,
                scope_kind, runtime_mode, cost_accounting_pending, process_loss_retry_count,
                continuation_attempt, scheduled_retry_attempt, accounting_attempt_count, next_event_seq
            ) VALUES (
                $1, $2, $3, 'telegram', 'succeeded', $4,
                NOW() - ($5 || ' seconds')::interval, NOW(), $6, $7::jsonb,
                $8::jsonb, 'company', 'direct', false, 0, 0, 0, 0, 1
            )
            """,
            run_id,
            company_uuid,
            agent_uuid,
            f"Telegram interaction with user {user_id}",
            str(max(0.1, duration_sec)),
            summary_text,
            usage_payload,
            result_payload,
        )

        # 2. Insert into activity log
        await conn.execute(
            """
            INSERT INTO activity_log (
                id, company_id, actor_type, actor_id, action, entity_type, entity_id,
                agent_id, run_id, details, created_at, responsible_user_id
            ) VALUES (
                gen_random_uuid(), $1, 'agent', $2, 'agent.telegram_turn', 'agent', $2,
                $3, $4, $5::jsonb, NOW(), $6
            )
            """,
            company_uuid,
            str(agent_id),
            agent_uuid,
            run_id,
            activity_details,
            DEFAULT_RESPONSIBLE_USER_ID,
        )

        # 3. Update agent heartbeat and spend
        await conn.execute(
            """
            UPDATE agents
            SET last_heartbeat_at = NOW(),
                status = 'idle',
                spent_monthly_cents = spent_monthly_cents + $2
            WHERE id = $1
            """,
            agent_uuid,
            cost_cents,
        )

        logger.info("⚡ [Paperclip Bridge] Recorded Telegram turn into Paperclip (run_id: %s)", run_id)
        return True
    except Exception as err:
        logger.warning("⚠️ [Paperclip Bridge] Failed to record turn in Paperclip: %s", err)
        return False
    finally:
        if conn:
            try:
                await conn.close()
            except Exception:
                pass

async def list_paperclip_issues(
    status: Optional[str] = None,
    company_id: str = DEFAULT_COMPANY_ID,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Queries actionable issues from Paperclip Kanban board.
    """
    db_url = get_paperclip_db_url()
    if not db_url:
        return []

    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        query = """
            SELECT id, identifier, title, status, priority, created_at
            FROM issues
            WHERE company_id = $1
        """
        params = [uuid.UUID(company_id)]
        if status:
            query += " AND status = $2"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        rows = await conn.fetch(query, *params)
        await conn.close()
        return [
            {
                "id": str(r["id"]),
                "identifier": r["identifier"],
                "title": r["title"],
                "status": r["status"],
                "priority": r["priority"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    except Exception as err:
        logger.warning("Error querying Paperclip issues: %s", err)
        return []

async def create_paperclip_issue(
    title: str,
    description: str = "",
    priority: str = "medium",
    company_id: str = DEFAULT_COMPANY_ID,
    assignee_agent_id: str = DEFAULT_HERMES_AGENT_ID,
) -> Optional[Dict[str, Any]]:
    """
    Creates a new issue in Paperclip directly from conversational Hermes requests.
    """
    db_url = get_paperclip_db_url()
    if not db_url:
        return None

    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)

        # 1. Resolve issue prefix & calculate next sequence
        company_row = await conn.fetchrow(
            "SELECT issue_prefix FROM companies WHERE id = $1",
            uuid.UUID(company_id),
        )
        prefix = company_row["issue_prefix"] if company_row else "BAI"

        count_row = await conn.fetchrow(
            "SELECT COUNT(*) FROM issues WHERE company_id = $1",
            uuid.UUID(company_id),
        )
        seq = (count_row[0] if count_row else 0) + 1
        identifier = f"{prefix}-{seq}"

        issue_id = uuid.uuid4()
        await conn.execute(
            """
            INSERT INTO issues (
                id, company_id, identifier, title, description, status, priority,
                assignee_agent_id, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, 'todo', $6, $7, NOW(), NOW()
            )
            """,
            issue_id,
            uuid.UUID(company_id),
            identifier,
            title,
            description,
            priority,
            uuid.UUID(assignee_agent_id),
        )

        # Log activity
        await conn.execute(
            """
            INSERT INTO activity_log (
                id, company_id, actor_type, actor_id, action, entity_type, entity_id,
                agent_id, details, created_at, responsible_user_id
            ) VALUES (
                gen_random_uuid(), $1, 'agent', $2, 'issue.created', 'issue', $3,
                $4, $5::jsonb, NOW(), $6
            )
            """,
            uuid.UUID(company_id),
            str(assignee_agent_id),
            str(issue_id),
            uuid.UUID(assignee_agent_id),
            json.dumps({"identifier": identifier, "title": title, "source": "telegram_hermes"}),
            DEFAULT_RESPONSIBLE_USER_ID,
        )

        await conn.close()
        logger.info("📋 [Paperclip Bridge] Created issue %s: %s", identifier, title)
        return {
            "id": str(issue_id),
            "identifier": identifier,
            "title": title,
            "status": "todo",
            "priority": priority,
        }
    except Exception as err:
        logger.warning("Error creating Paperclip issue: %s", err)
        return None
