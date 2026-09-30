import postgres from "postgres";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const sqlPath = resolve(__dirname, "schema.sql");
const sqlContent = readFileSync(sqlPath, "utf-8");

const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  console.log("DATABASE_URL not set, skipping live database migration");
  process.exit(0);
}

const sql = postgres(dbUrl, { max: 1 });
try {
  console.log("Applying schema.sql to PostgreSQL...");
  await sql.unsafe(sqlContent);
  console.log("✓ Schema applied successfully (PostgreSQL 18 DDL)");
} catch (err) {
  console.error("Migration error:", err);
  process.exit(1);
} finally {
  await sql.end();
}
