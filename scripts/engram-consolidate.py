#!/usr/bin/env python3
"""
engram-consolidate.py — Consolidación y Normalización Atómica de Memoria Engram
Fusiona las observaciones históricas y recientes bajo la identidad canónica 'glamur'.
"""
import sqlite3
import os
import shutil
import sys

def consolidate(db_historical: str, db_recent: str, target_db: str, canonical_project: str = "glamur"):
    print(f"• Consolidando bases SQLite en: {target_db}")
    print(f"  - Histórica: {db_historical}")
    print(f"  - Reciente : {db_recent}")
    print(f"  - Proyecto : {canonical_project}")

    target_dir = os.path.dirname(target_db)
    os.makedirs(target_dir, exist_ok=True)
    if os.path.exists(target_db):
        os.remove(target_db)

    # Iniciar copiando la base histórica
    shutil.copy2(db_historical, target_db)

    conn_target = sqlite3.connect(target_db)
    cur_target = conn_target.cursor()

    # Normalizar todo en la base destino al proyecto canónico
    cur_target.execute("UPDATE sessions SET project = ?;", (canonical_project,))
    cur_target.execute("UPDATE observations SET project = ?;", (canonical_project,))
    cur_target.execute("UPDATE user_prompts SET project = ?;", (canonical_project,))
    conn_target.commit()

    # Leer base reciente (chassis)
    conn_recent = sqlite3.connect(db_recent)
    cur_recent = conn_recent.cursor()

    # Sincronizar sesiones
    cur_recent.execute("SELECT id, directory, started_at, ended_at, summary FROM sessions;")
    for row in cur_recent.fetchall():
        sid, d, start, end, summ = row
        cur_target.execute(
            "INSERT OR IGNORE INTO sessions (id, project, directory, started_at, ended_at, summary) VALUES (?, ?, ?, ?, ?, ?);",
            (sid, canonical_project, d, start, end, summ)
        )

    # Sincronizar observaciones
    cols = [
        "sync_id", "session_id", "type", "title", "content", "tool_name", "project",
        "scope", "topic_key", "normalized_hash", "revision_count", "duplicate_count",
        "last_seen_at", "pinned", "created_at", "updated_at", "deleted_at",
        "review_after", "expires_at", "embedding", "embedding_model", "embedding_created_at"
    ]
    query_select = f"SELECT {', '.join(cols)} FROM observations ORDER BY id ASC;"
    cur_recent.execute(query_select)
    recent_rows = cur_recent.fetchall()

    inserted_count = 0
    for r in recent_rows:
        sync_id = r[0]
        cur_target.execute("SELECT id FROM observations WHERE sync_id = ?;", (sync_id,))
        if cur_target.fetchone():
            continue
        row_dict = list(r)
        # Forzar project canónico
        row_dict[6] = canonical_project
        placeholders = ", ".join(["?"] * len(cols))
        cur_target.execute(
            f"INSERT INTO observations ({', '.join(cols)}) VALUES ({placeholders});",
            row_dict
        )
        inserted_count += 1

    conn_target.commit()

    # Integridad y estadísticas
    cur_target.execute("SELECT count(*) FROM observations;")
    total_obs = cur_target.fetchone()[0]
    cur_target.execute("SELECT DISTINCT project, count(*) FROM observations GROUP BY project;")
    proj_counts = cur_target.fetchall()
    cur_target.execute("PRAGMA integrity_check;")
    integrity = cur_target.fetchone()[0]

    conn_recent.close()
    conn_target.close()

    print(f"✓ Consolidación exitosa:")
    print(f"  - Nuevas observaciones insertadas: {inserted_count}")
    print(f"  - Total observaciones consolidadas: {total_obs}")
    print(f"  - Desglose por proyecto: {proj_counts}")
    print(f"  - Verificación de integridad SQLite: {integrity}")

    if integrity != "ok":
        raise RuntimeError(f"Error de integridad en SQLite: {integrity}")

if __name__ == "__main__":
    db_hist = "/var/www/baiosfera/0ZEROPS-AGY/glamur/engram/engram.db"
    db_rec = "/var/www/localstorage/engram/zerops-astrobranding/engram.db"
    target = "/var/www/localstorage/engram/glamur/engram.db"
    consolidate(db_hist, db_rec, target, "glamur")
