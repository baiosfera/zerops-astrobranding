import { defineAction, ActionError } from "astro:actions";
import { z } from "astro:schema";
import {
  getDb,
  products,
  productVariants,
  loginWithAdminPassword,
  requestAdminOtp,
  verifyAdminOtp,
  requestAdminWhatsAppOtp,
  verifyAdminWhatsAppOtp,
  revokeAdminSession,
  notifySuperadminAudit,
  eq,
  desc,
  and,
} from "@astrobranding/database";
import { existsSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

function getStorageDir(): string {
  if (existsSync("/mnt/localstorage")) {
    const dir = "/mnt/localstorage/products";
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    return dir;
  }
  const fallback = "/var/www/localstorage/products";
  if (!existsSync(fallback)) mkdirSync(fallback, { recursive: true });
  return fallback;
}

export const server = {
  loginWithPassword: defineAction({
    input: z.object({
      identifier: z.string().min(1),
      password: z.string().min(1),
    }),
    handler: async ({ identifier, password }, context) => {
      const ip =
        context.request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
        context.clientAddress ||
        "N/A";
      const userAgent = context.request.headers.get("user-agent") || "N/A";

      const res = await loginWithAdminPassword(identifier, password, { ip, userAgent });
      if (res.success && res.sessionToken) {
        context.cookies.set("admin_session", res.sessionToken, {
          path: "/adminn",
          httpOnly: true,
          secure: true,
          sameSite: "lax",
          maxAge: 7 * 24 * 60 * 60, // 7 days
        });
      }
      return res;
    },
  }),

  requestWhatsAppOtp: defineAction({
    input: z.object({
      phone: z.string().min(7),
    }),
    handler: async ({ phone }) => {
      const res = await requestAdminWhatsAppOtp(phone);
      return res;
    },
  }),

  verifyWhatsAppOtp: defineAction({
    input: z.object({
      phone: z.string().min(7),
      code: z.string().length(6),
    }),
    handler: async ({ phone, code }, context) => {
      const ip =
        context.request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
        context.clientAddress ||
        "N/A";
      const userAgent = context.request.headers.get("user-agent") || "N/A";

      const res = await verifyAdminWhatsAppOtp(phone, code, { ip, userAgent });
      if (res.success && res.sessionToken) {
        context.cookies.set("admin_session", res.sessionToken, {
          path: "/adminn",
          httpOnly: true,
          secure: true,
          sameSite: "lax",
          maxAge: 7 * 24 * 60 * 60, // 7 days
        });
      }
      return res;
    },
  }),

  requestOtp: defineAction({
    input: z.object({
      telegramUserId: z.union([z.number(), z.string().regex(/^\d+$/).transform(Number)]),
    }),
    handler: async ({ telegramUserId }) => {
      const res = await requestAdminOtp(telegramUserId);
      return res;
    },
  }),

  verifyOtp: defineAction({
    input: z.object({
      telegramUserId: z.union([z.number(), z.string().regex(/^\d+$/).transform(Number)]),
      code: z.string().length(6),
    }),
    handler: async ({ telegramUserId, code }, context) => {
      const ip =
        context.request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
        context.clientAddress ||
        "N/A";
      const userAgent = context.request.headers.get("user-agent") || "N/A";

      const res = await verifyAdminOtp(telegramUserId, code, { ip, userAgent });
      if (res.success && res.sessionToken) {
        context.cookies.set("admin_session", res.sessionToken, {
          path: "/adminn",
          httpOnly: true,
          secure: true,
          sameSite: "lax",
          maxAge: 7 * 24 * 60 * 60, // 7 days
        });
      }
      return res;
    },
  }),

  logout: defineAction({
    input: z.object({}).optional(),
    handler: async (_input, context) => {
      const sessionToken = context.cookies.get("admin_session")?.value;
      if (sessionToken) {
        await revokeAdminSession(sessionToken);
        context.cookies.delete("admin_session", { path: "/adminn" });
      }
      return { success: true };
    },
  }),

  toggleProductStatus: defineAction({
    input: z.object({
      productId: z.string().uuid(),
      isActive: z.number().min(0).max(1),
    }),
    handler: async ({ productId, isActive }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({
          code: "UNAUTHORIZED",
          message: "Sesión no autenticada en /adminn.",
        });
      }

      const db = getDb();
      const [prod] = await db.select().from(products).where(eq(products.id, productId)).limit(1);
      if (!prod) {
        throw new ActionError({
          code: "NOT_FOUND",
          message: "Producto no encontrado.",
        });
      }

      await db.update(products).set({ isActive, updatedAt: new Date() }).where(eq(products.id, productId));

      const statusName = isActive === 1 ? "activado" : "desactivado (soft-delete)";
      notifySuperadminAudit(
        `👁️ <b>Catálogo /adminn</b>\nProducto <b>${prod.name}</b> ${statusName} por <b>${adminUser.name}</b> (${adminUser.role}).`
      ).catch(() => {});

      return { success: true, isActive };
    },
  }),

  updateProduct: defineAction({
    input: z.object({
      id: z.string().uuid(),
      name: z.string().min(1),
      description: z.string().optional(),
      basePrice: z.number().positive(),
      category: z.string().min(1),
      slug: z.string().min(1),
    }),
    handler: async ({ id, name, description, basePrice, category, slug }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({
          code: "UNAUTHORIZED",
          message: "Sesión no autenticada en /adminn.",
        });
      }

      const db = getDb();
      const [current] = await db.select().from(products).where(eq(products.id, id)).limit(1);
      if (!current) {
        throw new ActionError({
          code: "NOT_FOUND",
          message: "Producto no encontrado.",
        });
      }

      // RBAC: Only superadmin can mutate slugs
      let finalSlug = current.slug;
      if (slug !== current.slug) {
        if (adminUser.role !== "superadmin") {
          throw new ActionError({
            code: "FORBIDDEN",
            message: "Sólo el superadministrador puede alterar los slugs permanentes.",
          });
        }
        finalSlug = slug.trim().toLowerCase();
      }

      // Check if price changed
      if (basePrice !== current.basePrice) {
        notifySuperadminAudit(
          `💰 <b>Cambio de precio en /adminn</b>\nProducto: <b>${current.name}</b>\nPrecio anterior: $${current.basePrice.toLocaleString("es-CO")} COP\nNuevo precio: $${basePrice.toLocaleString("es-CO")} COP\nModificado por: <b>${adminUser.name}</b> (${adminUser.role})`
        ).catch(() => {});
      }

      await db
        .update(products)
        .set({
          name: name.trim(),
          description: description?.trim() || null,
          basePrice,
          category: category.trim(),
          slug: finalSlug,
          updatedAt: new Date(),
        })
        .where(eq(products.id, id));

      return { success: true };
    },
  }),

  createProduct: defineAction({
    input: z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      basePrice: z.number().positive(),
      category: z.string().min(1),
      imageBase64: z.string().optional(),
      imageName: z.string().optional(),
    }),
    handler: async ({ name, description, basePrice, category, imageBase64, imageName }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({
          code: "UNAUTHORIZED",
          message: "Sesión no autenticada en /adminn.",
        });
      }

      const db = getDb();

      // Compute base slug
      let baseSlug = name
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");

      if (!baseSlug) baseSlug = `producto-${Date.now()}`;

      // Check if active slug collision exists
      const existing = await db
        .select()
        .from(products)
        .where(and(eq(products.slug, baseSlug), eq(products.isActive, 1)))
        .limit(1);

      if (existing.length > 0) {
        baseSlug = `${baseSlug}-${Math.floor(1000 + Math.random() * 9000)}`;
      }

      let imageUrls: string[] = [];
      if (imageBase64 && imageName) {
        try {
          const buffer = Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""), "base64");
          const ext = imageName.split(".").pop()?.toLowerCase() || "jpg";
          const safeFileName = `admin_${Date.now()}_${Math.random().toString(36).substring(2, 7)}.${ext}`;
          const storageDir = getStorageDir();
          const targetPath = join(storageDir, safeFileName);
          writeFileSync(targetPath, buffer);
          imageUrls.push(`/images/products/${safeFileName}`);
        } catch (imgErr) {
          console.error("[Action createProduct] Image save error:", imgErr);
        }
      }

      const [newProd] = await db
        .insert(products)
        .values({
          name: name.trim(),
          slug: baseSlug,
          description: description?.trim() || null,
          category: category.trim(),
          basePrice,
          images: imageUrls,
          isActive: 1,
        })
        .returning();

      // Insert default variant
      await db.insert(productVariants).values({
        productId: newProd.id,
        sku: `${baseSlug.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8)}-UNICO`,
        size: "Única",
        color: "Estándar",
        price: basePrice,
        stock: 10,
      });

      notifySuperadminAudit(
        `✨ <b>Nuevo producto creado en /adminn</b>\nNombre: <b>${newProd.name}</b>\nSlug: <code>${newProd.slug}</code>\nPrecio: $${basePrice.toLocaleString("es-CO")} COP\nCreador: <b>${adminUser.name}</b> (${adminUser.role})`
      ).catch(() => {});

      return { success: true, product: newProd };
    },
  }),

  deleteProductHard: defineAction({
    input: z.object({
      productId: z.string().uuid(),
    }),
    handler: async ({ productId }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({
          code: "UNAUTHORIZED",
          message: "Sesión no autenticada en /adminn.",
        });
      }

      // Strict RBAC: only superadmin can hard delete
      if (adminUser.role !== "superadmin") {
        throw new ActionError({
          code: "FORBIDDEN",
          message:
            "Acción denegada: Sólo el superadministrador puede eliminar productos de forma permanente. Como comerciante puedes desactivar el producto.",
        });
      }

      const db = getDb();
      const [prod] = await db.select().from(products).where(eq(products.id, productId)).limit(1);
      if (!prod) {
        throw new ActionError({
          code: "NOT_FOUND",
          message: "Producto no encontrado.",
        });
      }

      await db.delete(products).where(eq(products.id, productId));

      notifySuperadminAudit(
        `🗑️ <b>Producto eliminado permanentemente en /adminn</b>\nProducto: <b>${prod.name}</b> (slug: <code>${prod.slug}</code>)\nEliminado por: <b>${adminUser.name}</b> (${adminUser.role})`
      ).catch(() => {});

      return { success: true };
    },
  }),
};
