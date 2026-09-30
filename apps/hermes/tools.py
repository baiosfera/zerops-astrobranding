"""
Hermes-Agent Execution Tools
Sovereign Integration Mesh: Connects Hermes-Agent to PostgreSQL 18, NATS JetStream, and the AstroBranding Central Engine.
"""
import os
import json
import uuid
import httpx
from typing import Dict, Any, Optional

API_BASE = os.getenv("API_BASE_URL", "http://astrobranding:3000")
DATABASE_URL = os.getenv("DATABASE_URL", "")
NATS_URL = os.getenv("NATS_URL") or os.getenv("ZCP_NATS_URL", "nats://nats:4222")

async def get_system_health() -> dict:
    """Check health across mesh components"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{API_BASE}/health")
            return res.json()
        except Exception as e:
            return {"service": "hermes-agent", "status": "autonomous", "upstream_error": str(e)}

async def calculate_natal_chart(client_id: str, ayanamsha: str = "tropical") -> dict:
    """Calculate chart or trigger computation via internal engine"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(
                f"{API_BASE}/api/astrology/chart",
                json={"clientId": client_id, "ayanamsha": ayanamsha, "houseSystem": "placidus"}
            )
            return res.json()
        except Exception as e:
            return {"error": str(e)}

async def get_client_gold_feeds(client_id: str) -> dict:
    """Fetch XML Gold Feeds directly from PostgreSQL 18 or API fallback"""
    if DATABASE_URL:
        try:
            import asyncpg
            conn = await asyncpg.connect(DATABASE_URL)
            rows = await conn.fetch(
                "SELECT feed_name, feed_xml FROM client_feeds WHERE client_id = $1",
                uuid.UUID(client_id)
            )
            await conn.close()
            feeds = {row["feed_name"]: row["feed_xml"] for row in rows}
            return {"status": "ok", "client_id": client_id, "source": "postgres_direct", "feeds": feeds}
        except Exception as err:
            pass

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{API_BASE}/api/v1/feeds/{client_id}")
            return res.json()
        except Exception as e:
            return {"error": str(e)}

async def query_client_dumps(client_id: str, shard_name: Optional[str] = None) -> dict:
    """Query 15-shard JSONB client dumps directly from PostgreSQL 18"""
    if not DATABASE_URL:
        return {"status": "error", "message": "DATABASE_URL not configured"}
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        if shard_name:
            query = f"SELECT {shard_name} FROM client_dumps WHERE client_id = $1"
            row = await conn.fetchrow(query, uuid.UUID(client_id))
            await conn.close()
            return {
                "status": "ok",
                "client_id": client_id,
                "shard": shard_name,
                "data": json.loads(row[0]) if row and row[0] else None
            }
        else:
            row = await conn.fetchrow("SELECT * FROM client_dumps WHERE client_id = $1", uuid.UUID(client_id))
            await conn.close()
            return {"status": "ok", "client_id": client_id, "data": dict(row) if row else None}
    except Exception as err:
        return {"status": "error", "message": f"PostgreSQL query failed: {str(err)}"}

async def trigger_universal_extraction(birth_data: dict, dry_run: bool = False) -> dict:
    """Trigger or dispatch the 15-Shard Universal Extraction across federated astrology engines"""
    task_id = str(uuid.uuid4())
    payload = {
        "task_id": task_id,
        "action": "astrology.calculate.v1",
        "client": birth_data,
        "dry_run": dry_run
    }
    try:
        from nats.aio.client import Client as NATS
        nc = NATS()
        await nc.connect(NATS_URL)
        js = nc.jetstream()
        await js.publish(
            "astrology.requests",
            json.dumps(payload).encode("utf-8"),
            headers={"Nats-Msg-Id": task_id}
        )
        await nc.close()
        return {"status": "dispatched", "task_id": task_id, "message": "Astrological calculation queued on NATS."}
    except Exception:
        # Fallback to direct HTTP if NATS connection is unavailable
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(
                    f"{API_BASE}/api/v1/extract?dryRun={'true' if dry_run else 'false'}",
                    json=birth_data
                )
                return res.json()
            except Exception as e:
                return {"status": "error", "error": str(e)}

async def send_whatsapp_otp(phone: str, client_name: str) -> dict:
    """Send OTP via Evolution API or internal broker"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(
                f"{API_BASE}/api/whatsapp/otp",
                json={"phoneNumber": phone, "clientName": client_name, "template": "otp_verification"}
            )
            return res.json()
        except Exception as e:
            return {"error": str(e)}
