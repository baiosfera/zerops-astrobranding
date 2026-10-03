#!/usr/bin/env python3
"""
Ingest Client Dumps & Feeds into PostgreSQL 18 Database.
Reads client_dumps_15_shards.json and feeds, then performs an idempotent UPSERT.
"""

import json
import os
from pathlib import Path
import subprocess
import sys


def load_env(env_path="/etc/environment"):
    env = dict(os.environ)
    p = Path(env_path)
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in env:
                        env[k.strip()] = v.strip().strip("'\"")
    return env


def main():
    env = load_env()
    db_url = env.get("DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("db_connectionString")
    if not db_url:
        print("❌ Error: DATABASE_URL o db_connectionString no encontrada en variables de Zerops ni /etc/environment", file=sys.stderr)
        sys.exit(1)

    dumps_json_path = Path("/var/www/baiosfera/ASTROLOGÍA/DIAG/JUAN_DAMAREN_AGY/raw/json/dumps/client_dumps_15_shards.json")
    if not dumps_json_path.exists():
        print(f"❌ Error: {dumps_json_path} no existe", file=sys.stderr)
        sys.exit(1)

    with open(dumps_json_path, "r", encoding="utf-8") as f:
        dumps_15 = json.load(f)

    birth_meta = dumps_15.get("birth_metadata", {})
    client_name = birth_meta.get("name", "Jonathan Alzate Quintero")
    current_name = birth_meta.get("preferred_name", "JUAN DEN KREISS DAMAREN SANKANA")
    email = "juan.damaren@glamur.ai"
    phone = "+573000000000"
    birth_date = f"{birth_meta.get('year', 1984):04d}-{int(birth_meta.get('month', 6)):02d}-{int(birth_meta.get('day', 9)):02d}"
    birth_time = f"{int(birth_meta.get('hour', 11)):02d}:{int(birth_meta.get('minute', 45)):02d}"
    birth_city = birth_meta.get("city", "Bogota")
    birth_country = "Colombia"
    lat = str(birth_meta.get("lat", 4.5882307))
    lon = str(birth_meta.get("lng", -74.0853965))

    print(f"👤 Ingestando cliente: {client_name} ({current_name}) [{email}]...")

    # 1. Upsert Client via psql
    client_sql = f"""
    INSERT INTO clients (name, email, phone, birth_date, birth_time, birth_city, birth_country, latitude, longitude, status, updated_at)
    VALUES ('{client_name}', '{email}', '{phone}', '{birth_date}', '{birth_time}', '{birth_city}', '{birth_country}', '{lat}', '{lon}', 'active', NOW())
    ON CONFLICT (email) DO UPDATE SET
        name = EXCLUDED.name,
        birth_date = EXCLUDED.birth_date,
        birth_time = EXCLUDED.birth_time,
        birth_city = EXCLUDED.birth_city,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        updated_at = NOW()
    RETURNING id;
    """

    res = subprocess.run(["psql", db_url, "-t", "-A", "-c", client_sql], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Error al insertar en clients: {res.stderr}", file=sys.stderr)
        sys.exit(1)

    client_id = [line.strip() for line in res.stdout.strip().splitlines() if "-" in line][0]
    print(f"✅ Cliente registrado con ID UUID: {client_id}")

    # 2. Ingest 15 JSONB Shards into client_dumps
    columns = [
        "client_id", "birth_metadata", "shard_western_tropical", "shard_western_sidereal",
        "shard_vedic_jyotish", "shard_vedic_dashas", "shard_bazi_metaphysics",
        "shard_ziwei_fengshui", "shard_kabbalah_gematria", "shard_hebrew_zmanim",
        "shard_human_design", "shard_cosmobiology_midpoints", "shard_nasa_ephemerides",
        "shard_astrocartography_acg", "shard_business_penta_org", "shard_partner_synastry",
        "shard_predictive_electional"
    ]

    # Pre-clean existing dumps for this client
    subprocess.run(["psql", db_url, "-c", f"DELETE FROM client_dumps WHERE client_id = '{client_id}';"], check=True)

    # Use python with temporary json files or psql stdin
    # We will write a python script with direct psycopg or json string piping
    temp_sql_file = Path("/tmp/ingest_dumps.sql")
    with open(temp_sql_file, "w", encoding="utf-8") as f:
        f.write(f"INSERT INTO client_dumps ({', '.join(columns)})\nVALUES (\n")
        f.write(f"'{client_id}'::uuid,\n")
        
        shard_keys = columns[1:]
        val_clauses = []
        for k in shard_keys:
            val = dumps_15.get(k, {})
            # Escapar comillas simples para SQL literal
            escaped_json = json.dumps(val, ensure_ascii=False).replace("'", "''")
            val_clauses.append(f"'{escaped_json}'::jsonb")
        f.write(",\n".join(val_clauses))
        f.write("\n);\n")

    res_dump = subprocess.run(["psql", db_url, "-f", str(temp_sql_file)], capture_output=True, text=True)
    temp_sql_file.unlink(missing_ok=True)

    if res_dump.returncode != 0:
        print(f"❌ Error al insertar en client_dumps: {res_dump.stderr}", file=sys.stderr)
        sys.exit(1)

    print("✅ 15 Shards JSONB ingestados con éxito en client_dumps!")

    # 3. Ingest feeds into client_feeds
    feeds_dir = Path("/var/www/baiosfera/ASTROLOGÍA/DIAG/JUAN_DAMAREN_AGY/raw/feeds")
    if feeds_dir.exists():
        subprocess.run(["psql", db_url, "-c", f"DELETE FROM client_feeds WHERE client_id = '{client_id}';"], check=True)
        count_feeds = 0
        for feed_file in feeds_dir.glob("*.md"):
            content = feed_file.read_text(encoding="utf-8").replace("'", "''")
            feed_type = feed_file.stem
            tokens = len(content) // 4
            feed_sql = f"""
            INSERT INTO client_feeds (client_id, feed_type, xml_payload, token_estimate)
            VALUES ('{client_id}', '{feed_type}', '{content}', {tokens});
            """
            subprocess.run(["psql", db_url, "-c", feed_sql], check=True)
            count_feeds += 1
        print(f"✅ {count_feeds} feeds ingestados en client_feeds!")

    print("🎉 Ingesta en PostgreSQL 18 completada exitosamente (exit code 0).")


if __name__ == "__main__":
    main()
