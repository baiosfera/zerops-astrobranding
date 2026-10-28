import postgres from "postgres";

/**
 * Universal Agnostic Seed Engine — Zerops Astrobranding
 * 
 * SSoT & Ingestion Governance Contract:
 * 1. PostgreSQL is the SOLE System of Record (SoR) for live merchant data (prices, stock, images).
 * 2. On conflict, this seed updates ONLY descriptive metadata (name, description, category).
 * 3. NEVER overwrites base_price, stock, images, or is_active if the product exists in the DB,
 *    protecting live updates made via Telegram (Hermes Agent), CRM, or Admin UI.
 * 4. Pass `--force-prices` to explicitly override database prices from code.
 */

const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  console.log("ℹ️ DATABASE_URL not set, skipping seed");
  process.exit(0);
}

const sql = postgres(dbUrl, { max: 1 });
const forcePrices = process.argv.includes("--force-prices");

export interface SeedCatalogItem {
  slug: string;
  name: string;
  description: string;
  category: string;
  base_price: number;
  images: string[];
  variants?: Array<{
    sku: string;
    size: string;
    color: string;
    price: number;
    stock: number;
  }>;
}

export async function seedCatalog(items: SeedCatalogItem[]) {
  console.log(`Seeding catalog items (count=${items.length}, forcePrices=${forcePrices})...`);

  for (const item of items) {
    let p;
    if (forcePrices) {
      [p] = await sql`
        INSERT INTO products (slug, name, description, category, base_price, images, is_active)
        VALUES (${item.slug}, ${item.name}, ${item.description}, ${item.category}, ${item.base_price}, ${JSON.stringify(item.images)}::jsonb, 1)
        ON CONFLICT (slug) DO UPDATE SET
          name = EXCLUDED.name,
          description = EXCLUDED.description,
          category = EXCLUDED.category,
          base_price = EXCLUDED.base_price,
          images = EXCLUDED.images
        RETURNING id;
      `;
    } else {
      [p] = await sql`
        INSERT INTO products (slug, name, description, category, base_price, images, is_active)
        VALUES (${item.slug}, ${item.name}, ${item.description}, ${item.category}, ${item.base_price}, ${JSON.stringify(item.images)}::jsonb, 1)
        ON CONFLICT (slug) DO UPDATE SET
          name = EXCLUDED.name,
          description = EXCLUDED.description,
          category = EXCLUDED.category
        RETURNING id;
      `;
    }

    if (item.variants && item.variants.length > 0) {
      for (const v of item.variants) {
        if (forcePrices) {
          await sql`
            INSERT INTO product_variants (product_id, sku, size, color, price, stock)
            VALUES (${p.id}, ${v.sku}, ${v.size}, ${v.color}, ${v.price}, ${v.stock})
            ON CONFLICT (sku) DO UPDATE SET
              size = EXCLUDED.size,
              color = EXCLUDED.color,
              price = EXCLUDED.price,
              stock = EXCLUDED.stock;
          `;
        } else {
          await sql`
            INSERT INTO product_variants (product_id, sku, size, color, price, stock)
            VALUES (${p.id}, ${v.sku}, ${v.size}, ${v.color}, ${v.price}, ${v.stock})
            ON CONFLICT (sku) DO UPDATE SET
              size = EXCLUDED.size,
              color = EXCLUDED.color;
          `;
        }
      }
    }
  }

  console.log("✓ Additive Seed completed successfully (field-level ownership respected).");
}

async function main() {
  // Standalone execution entrypoint:
  // Client projects extend or supply their items; by default operates as safe no-op if no items provided.
  console.log("Agnostic seed script executed.");
}

if (import.meta.main) {
  try {
    await main();
  } catch (err) {
    console.error("Seed execution error:", err);
    process.exit(1);
  } finally {
    await sql.end();
  }
}
