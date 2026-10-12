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
    // 1. Query leads table
    const leadQuery = `
      SELECT id, alias_nombre, email, corset_vip, vip_until, primer_pago_acreditado, ciudad, metadata, created_at
      FROM leads
      WHERE whatsapp = ANY($1::varchar[])
      LIMIT 1
    `;
    const leadRes = await pool.query(leadQuery, [formattedVariants]);

    // Query user table by phoneNumber
    const userQuery = `
      SELECT id, name, email, vip_until
      FROM "user"
      WHERE "phoneNumber" = ANY($1::varchar[])
      LIMIT 1
    `;
    const userRes = await pool.query(userQuery, [formattedVariants]);
    const userRow = userRes.rows[0];

    const now = new Date();

    if (leadRes.rows.length > 0) {
      const lead = leadRes.rows[0];
      result.id = lead.id;
      result.alias = lead.alias_nombre || userRow?.name || undefined;
      result.isRegistered = Boolean(lead.alias_nombre || lead.email || lead.primer_pago_acreditado || userRow?.id);

      const isPaid = Boolean(
        (lead.vip_until && new Date(lead.vip_until) > now) ||
        (lead.corset_vip && lead.primer_pago_acreditado) ||
        (lead.metadata?.tags && lead.metadata.tags.includes("vip_activo")) ||
        (userRow?.vip_until && new Date(userRow.vip_until) > now)
      );

      result.isPaidVip = isPaid;
      result.isVip = isPaid;
      result.isPossibleVip = Boolean(
        (lead.corset_vip || (lead.metadata?.tags && (lead.metadata.tags.includes("corset") || lead.metadata.tags.includes("posible vip")))) && !isPaid
      );
      result.vipUntil = lead.vip_until
        ? new Date(lead.vip_until).toISOString().split("T")[0]
        : (userRow?.vip_until ? new Date(userRow.vip_until).toISOString().split("T")[0] : null);

      // 2. Query event_tickets table
      if (lead.id) {
        const ticketsQuery = `
          SELECT evento, tipo_entrada, monto_pagado, estado, created_at
          FROM event_tickets
          WHERE lead_id = $1
          ORDER BY created_at DESC
          LIMIT 10
        `;
        const ticketsRes = await pool.query(ticketsQuery, [lead.id]);
        result.totalEvents = ticketsRes.rows.length;
        result.pastTickets = ticketsRes.rows.map((row) => ({
          evento: row.evento,
          tipo_entrada: row.tipo_entrada || "General",
          monto_pagado: String(row.monto_pagado || "0"),
          estado: row.estado || "confirmado",
          fecha: new Date(row.created_at).toISOString().split("T")[0],
        }));
      }
    } else if (userRow) {
      result.alias = userRow.name;
      result.isRegistered = true;
      const isPaid = Boolean(userRow.vip_until && new Date(userRow.vip_until) > now);
      result.isPaidVip = isPaid;
      result.isVip = isPaid;
      result.isPossibleVip = false;
      result.vipUntil = userRow.vip_until ? new Date(userRow.vip_until).toISOString().split("T")[0] : null;
    }

    // 3. Query afiliados table
    const affQuery = `
      SELECT alias, clicks, referidos_pagados, entradas_ganadas
      FROM afiliados
      WHERE whatsapp = ANY($1::varchar[])
      LIMIT 1
    `;
    const affRes = await pool.query(affQuery, [formattedVariants]);
    if (affRes.rows.length > 0) {
      const aff = affRes.rows[0];
      result.affiliateAlias = aff.alias;
      result.affiliateClicks = aff.clicks || 0;
      result.affiliatePaidReferrals = aff.referidos_pagados || 0;
      result.affiliateFreeTicketsEarned = aff.entradas_ganadas || 0;
      result.affiliateShareUrl = `https://elplacerdecompartir.com/?ref=${aff.alias}`;
    }
  } catch (err) {
    console.error(`[PostgreSQL] Error fetching customer profile for ${rawPhone}:`, err);
  }

  return result;
}

export async function recordIncomingLead(phone: string, alias?: string): Promise<void> {
  const digits = phone.replace(/\D/g, "");
  try {
    const insertQuery = `
      INSERT INTO leads (whatsapp, alias_nombre, origen, created_at, updated_at)
      VALUES ($1, $2, 'whatsapp_bot', NOW(), NOW())
      ON CONFLICT (whatsapp) DO UPDATE
      SET updated_at = NOW(),
          alias_nombre = COALESCE(leads.alias_nombre, EXCLUDED.alias_nombre)
    `;
    await pool.query(insertQuery, [digits, alias || null]);
  } catch (err) {
    console.error(`[PostgreSQL] Error recording lead for ${digits}:`, err);
  }
}
