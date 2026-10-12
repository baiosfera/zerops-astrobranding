import pg from "pg";
const { Pool } = pg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

export interface CustomerData {
  id?: string;
  alias?: string;
  phone: string;
  email?: string;
  city?: string;
  role?: "hombre_solo" | "mujer_sola" | "pareja" | "otro" | string | null;
  isRegistered: boolean;
  isVip: boolean; // Backwards-compat: true only if isPaidVip
  isPaidVip: boolean;
  isPossibleVip: boolean;
  vipUntil: string | null;
  totalEvents: number;
  pastTickets: Array<{
    evento: string;
    tipo_entrada: string;
    monto_pagado: string;
    estado: string;
    fecha: string;
  }>;
  affiliateAlias?: string;
  affiliateClicks?: number;
  affiliatePaidReferrals?: number;
  affiliateFreeTicketsEarned?: number;
  affiliateShareUrl?: string;
}

let tablesCache: Set<string> | null = null;
let columnsCache: Map<string, Set<string>> = new Map();

async function getAvailableTables(): Promise<Set<string>> {
  if (tablesCache) return tablesCache;
  try {
    const res = await pool.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'");
    tablesCache = new Set(res.rows.map((r: any) => r.table_name));
    return tablesCache;
  } catch {
    return new Set();
  }
}

async function getTableColumns(tableName: string): Promise<Set<string>> {
  if (columnsCache.has(tableName)) return columnsCache.get(tableName)!;
  try {
    const res = await pool.query(
      "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = $1",
      [tableName]
    );
    const cols = new Set(res.rows.map((r: any) => r.column_name));
    columnsCache.set(tableName, cols);
    return cols;
  } catch {
    return new Set();
  }
}

export async function checkDbConnection(): Promise<boolean> {
  try {
    const res = await pool.query("SELECT 1 AS ok");
    return res.rows[0]?.ok === 1;
  } catch (err) {
    console.error("[PostgreSQL] Connection check failed:", err);
    return false;
  }
}

export async function getCustomerHistory(rawPhone: string): Promise<CustomerData> {
  const digits = rawPhone.replace(/\D/g, "");
  const last10 = digits.length >= 10 ? digits.slice(-10) : digits;
  const formattedVariants = [digits, `+${digits}`, digits.startsWith("57") ? digits.slice(2) : `57${digits}`];

  const result: CustomerData = {
    phone: digits,
    isRegistered: false,
    isVip: false,
    isPaidVip: false,
    isPossibleVip: false,
    vipUntil: null,
    totalEvents: 0,
    pastTickets: [],
  };

  try {
    const tables = await getAvailableTables();
    const canonicalBaseUrl = process.env.APP_URL || process.env.CANONICAL_URL || "https://elplacerdecompartir.com";

    // 1. Leads table (SSoT for web community and profile attributes)
    if (tables.has("leads")) {
      const leadCols = await getTableColumns("leads");
      const hasRol = leadCols.has("rol");
      const hasCity = leadCols.has("ciudad");
      const hasVipUntil = leadCols.has("vip_until");
      const hasCorsetVip = leadCols.has("corset_vip");
      const hasPrimerPago = leadCols.has("primer_pago_acreditado");
      const hasMeta = leadCols.has("metadata");

      const leadQuery = `
        SELECT id, alias_nombre, email
               ${hasRol ? ", rol" : ""}
               ${hasCity ? ", ciudad" : ""}
               ${hasVipUntil ? ", vip_until" : ""}
               ${hasCorsetVip ? ", corset_vip" : ""}
               ${hasPrimerPago ? ", primer_pago_acreditado" : ""}
               ${hasMeta ? ", metadata" : ""}
               , created_at, updated_at
        FROM leads
        WHERE (whatsapp = ANY($1::varchar[]) OR RIGHT(regexp_replace(whatsapp, '\\D', '', 'g'), 10) = $2)
        ORDER BY 
          CASE WHEN alias_nombre IS NOT NULL AND alias_nombre != '' THEN 0 ELSE 1 END,
          updated_at DESC NULLS LAST,
          created_at DESC
        LIMIT 1
      `;
      const leadRes = await pool.query(leadQuery, [formattedVariants, last10]);
      const leadRow = leadRes.rows[0];

      if (leadRow) {
        result.id = leadRow.id;
        result.alias = leadRow.alias_nombre || undefined;
        result.email = leadRow.email || undefined;
        result.city = leadRow.ciudad || undefined;
        result.role = leadRow.rol || undefined;
        result.isRegistered = Boolean(leadRow.alias_nombre || leadRow.email || leadRow.primer_pago_acreditado);

        const now = new Date();
        const isPaid = Boolean(
          (leadRow.vip_until && new Date(leadRow.vip_until) > now) ||
          (leadRow.corset_vip && leadRow.primer_pago_acreditado) ||
          (leadRow.metadata?.tags && leadRow.metadata.tags.includes("vip_activo"))
        );

        result.isPaidVip = isPaid;
        result.isVip = isPaid;
        result.isPossibleVip = Boolean(
          (leadRow.corset_vip || (leadRow.metadata?.tags && (leadRow.metadata.tags.includes("corset") || leadRow.metadata.tags.includes("posible vip")))) && !isPaid
        );
        result.vipUntil = leadRow.vip_until
          ? new Date(leadRow.vip_until).toISOString().split("T")[0]
          : null;

        // Tickets query
        if (tables.has("event_tickets") && leadRow.id) {
          try {
            const ticketsQuery = `
              SELECT evento, tipo_entrada, monto_pagado, estado, created_at
              FROM event_tickets
              WHERE lead_id = $1
              ORDER BY created_at DESC
              LIMIT 10
            `;
            const ticketsRes = await pool.query(ticketsQuery, [leadRow.id]);
            result.totalEvents = ticketsRes.rows.length;
            result.pastTickets = ticketsRes.rows.map((row: any) => ({
              evento: row.evento,
              tipo_entrada: row.tipo_entrada || "General",
              monto_pagado: String(row.monto_pagado || "0"),
              estado: row.estado || "confirmado",
              fecha: new Date(row.created_at).toISOString().split("T")[0],
            }));
          } catch {}
        }
      }
    }

    // 2. User table (Better-Auth / platform user)
    if (tables.has("user")) {
      try {
        const userQuery = `
          SELECT id, name, email, role, vip_until, "updatedAt"
          FROM "user"
          WHERE "phoneNumber" = ANY($1::varchar[]) OR RIGHT(regexp_replace("phoneNumber", '\\D', '', 'g'), 10) = $2
          ORDER BY "updatedAt" DESC NULLS LAST
          LIMIT 1
        `;
        const userRes = await pool.query(userQuery, [formattedVariants, last10]);
        const userRow = userRes.rows[0];

        if (userRow) {
          if (!result.id) result.id = userRow.id;
          if (!result.alias && userRow.name) result.alias = userRow.name;
          if (!result.email && userRow.email) result.email = userRow.email;
          if (!result.role && userRow.role) result.role = userRow.role;
          result.isRegistered = true;

          const now = new Date();
          if (userRow.vip_until && new Date(userRow.vip_until) > now) {
            result.isPaidVip = true;
            result.isVip = true;
            result.vipUntil = new Date(userRow.vip_until).toISOString().split("T")[0];
          }
        }
      } catch {}
    }

    // 3. Afiliados table (Ambassador / Referral SSoT)
    if (tables.has("afiliados")) {
      try {
        const affQuery = `
          SELECT alias, nombre, email, clicks, referidos_pagados, entradas_ganadas
          FROM afiliados
          WHERE (whatsapp = ANY($1::varchar[]) OR RIGHT(regexp_replace(whatsapp, '\\D', '', 'g'), 10) = $2)
          ORDER BY id DESC
          LIMIT 1
        `;
        const affRes = await pool.query(affQuery, [formattedVariants, last10]);
        if (affRes.rows.length > 0) {
          const aff = affRes.rows[0];
          result.affiliateAlias = aff.alias;
          result.affiliateClicks = aff.clicks || 0;
          result.affiliatePaidReferrals = aff.referidos_pagados || 0;
          result.affiliateFreeTicketsEarned = aff.entradas_ganadas || 0;
          result.affiliateShareUrl = `${canonicalBaseUrl}/?ref=${aff.alias}`;
          if (!result.alias && aff.nombre) result.alias = aff.nombre;
          if (!result.email && aff.email) result.email = aff.email;
        } else if (result.alias) {
          // Auto-provision affiliate code if registered lead has alias
          try {
            const generatedCode = await ensureAffiliateCode(result.alias, digits, result.email);
            result.affiliateAlias = generatedCode;
            result.affiliateClicks = 0;
            result.affiliatePaidReferrals = 0;
            result.affiliateFreeTicketsEarned = 0;
            result.affiliateShareUrl = `${canonicalBaseUrl}/?ref=${generatedCode}`;
          } catch (err) {
            console.warn(`[Afiliados:AutoProvision] Could not auto-provision for ${digits}:`, err);
          }
        }
      } catch {}
    }
  } catch (err) {
    console.error(`[PostgreSQL] Error fetching customer profile for ${rawPhone}:`, err);
  }

  return result;
}

export async function ensureAffiliateCode(aliasOrName: string, whatsapp?: string | null, email?: string | null): Promise<string> {
  const digits = whatsapp ? whatsapp.replace(/\D/g, "") : null;
  const last10 = digits && digits.length >= 10 ? digits.slice(-10) : digits;
  const variants = digits ? [digits, `+${digits}`, digits.startsWith("57") ? digits.slice(2) : `57${digits}`] : [];
  const cleanEmail = email ? email.trim().toLowerCase() : null;

  const tables = await getAvailableTables();
  if (!tables.has("afiliados")) {
    return aliasOrName || "embajador";
  }

  // 1. Check existing
  if (variants.length > 0 || cleanEmail) {
    const existing = await pool.query(
      `SELECT alias FROM afiliados 
       WHERE (whatsapp = ANY($1) OR RIGHT(regexp_replace(whatsapp, '\\D', '', 'g'), 10) = $2)
          OR (email = $3 AND $3 IS NOT NULL) 
       LIMIT 1`,
      [variants, last10, cleanEmail]
    );
    if (existing.rows.length > 0) {
      return existing.rows[0].alias;
    }
  }

  // 2. Derive base code
  const baseCode = (aliasOrName || "embajador")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, "") || "embajador";

  let candidate = baseCode;
  let attempt = 1;

  while (attempt <= 10) {
    const check = await pool.query(`SELECT 1 FROM afiliados WHERE LOWER(alias) = $1`, [candidate]);
    if (check.rows.length === 0) {
      await pool.query(
        `INSERT INTO afiliados (alias, nombre, whatsapp, email) VALUES ($1, $2, $3, $4) ON CONFLICT (alias) DO NOTHING`,
        [candidate, aliasOrName || "Embajador", digits ? `+${digits}` : null, cleanEmail]
      );
      return candidate;
    }
    candidate = `${baseCode}${Math.floor(100 + Math.random() * 900)}`;
    attempt++;
  }

  const fallbackCode = `embajador${Date.now().toString().slice(-5)}`;
  await pool.query(
    `INSERT INTO afiliados (alias, nombre, whatsapp, email) VALUES ($1, $2, $3, $4) ON CONFLICT (alias) DO NOTHING`,
    [fallbackCode, aliasOrName || "Embajador", digits ? `+${digits}` : null, cleanEmail]
  );
  return fallbackCode;
}

export async function recordIncomingLead(phone: string, alias?: string): Promise<void> {
  const digits = phone.replace(/\D/g, "");
  if (!digits) return;
  const last10 = digits.length >= 10 ? digits.slice(-10) : digits;
  const canonicalPhone = `+${digits}`;

  try {
    const tables = await getAvailableTables();
    if (!tables.has("leads")) return;

    // Check if lead already exists by any variant or suffix
    const existing = await pool.query(
      `SELECT id, whatsapp, alias_nombre FROM leads 
       WHERE whatsapp = ANY($1::varchar[]) 
          OR RIGHT(regexp_replace(whatsapp, '\\D', '', 'g'), 10) = $2
       LIMIT 1`,
      [[digits, canonicalPhone, `57${digits}`], last10]
    );

    if (existing.rows.length > 0) {
      const row = existing.rows[0];
      // Update existing lead without overwriting alias if already set
      await pool.query(
        `UPDATE leads 
         SET updated_at = NOW(),
             alias_nombre = COALESCE(leads.alias_nombre, NULLIF($2, ''))
         WHERE id = $1`,
        [row.id, alias || null]
      );
    } else {
      // Clean insert with canonical E.164 phone
      await pool.query(
        `INSERT INTO leads (whatsapp, alias_nombre, origen, created_at, updated_at)
         VALUES ($1, $2, 'whatsapp_bot', NOW(), NOW())
         ON CONFLICT (whatsapp) DO UPDATE
         SET updated_at = NOW(),
             alias_nombre = COALESCE(leads.alias_nombre, EXCLUDED.alias_nombre)`,
        [canonicalPhone, alias || null]
      );
    }
  } catch (err) {
    console.error(`[PostgreSQL] Error in recordIncomingLead for ${digits}:`, err);
  }
}

let evoPool: pg.Pool | null = null;
function getEvoPool(): pg.Pool | null {
  if (!evoPool && process.env.DATABASE_URL) {
    try {
      const parsed = new URL(process.env.DATABASE_URL);
      parsed.pathname = "/evogo_auth";
      evoPool = new Pool({
        connectionString: parsed.toString(),
        max: 3,
        idleTimeoutMillis: 30000,
      });
    } catch (err) {
      console.warn("[PostgreSQL] Could not initialize evogo_auth pool:", err);
    }
  }
  return evoPool;
}

export async function lookupPhoneByLidFromDb(lid: string): Promise<string | null> {
  const cleanLid = lid.replace(/\D/g, "");
  if (!cleanLid) return null;
  const pool = getEvoPool();
  if (!pool) return null;
  try {
    const res = await pool.query("SELECT pn FROM whatsmeow_lid_map WHERE lid = $1 LIMIT 1", [cleanLid]);
    if (res.rows.length > 0 && res.rows[0].pn) {
      return res.rows[0].pn.replace(/\D/g, "");
    }
  } catch (err) {
    // Ignore if table or database does not exist
  }
  return null;
}

export async function syncLidMappingsToValkey(redisClient: any): Promise<number> {
  const pool = getEvoPool();
  if (!pool) return 0;
  try {
    const res = await pool.query("SELECT lid, pn FROM whatsmeow_lid_map");
    if (res.rows.length === 0) return 0;
    const pipeline = redisClient.pipeline();
    for (const row of res.rows) {
      if (row.lid && row.pn) {
        pipeline.set(`wa:map:lid:${row.lid}`, row.pn, "EX", 2592000);
        pipeline.set(`wa:map:phone:${row.pn}`, row.lid, "EX", 2592000);
      }
    }
    await pipeline.exec();
    console.log(`[LID Sync] Successfully synced ${res.rows.length} LID mappings from PostgreSQL to Valkey`);
    return res.rows.length;
  } catch (err) {
    console.warn("[LID Sync] syncLidMappingsToValkey skipped or failed:", err);
    return 0;
  }
}

