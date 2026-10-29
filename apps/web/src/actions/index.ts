import { defineAction, ActionError } from "astro:actions";
import { z } from "astro:schema";
import {
  getDb,
  products,
  productVariants,
  services,
  bookings,
  siteSettings,
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
          path: "/",
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
          path: "/",
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
          path: "/",
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
        context.cookies.delete("admin_session", { path: "/" });
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
      slug: z.string().optional(),
      stock: z.number().int().min(0).optional(),
      imageBase64: z.string().optional(),
      imageName: z.string().optional(),
      removeImage: z.boolean().optional(),
    }),
    handler: async ({ id, name, description, basePrice, category, slug, stock, imageBase64, imageName, removeImage }, context) => {
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
      if (slug && slug.trim() && slug.trim() !== current.slug) {
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

      // Handle Image Mutation (Both Superadmin & Merchant)
      let finalImages = Array.isArray(current.images) ? [...current.images] : [];
      if (removeImage) {
        finalImages = [];
      }
      if (imageBase64 && imageName) {
        try {
          const buffer = Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""), "base64");
          const ext = imageName.split(".").pop()?.toLowerCase() || "jpg";
          const safeFileName = `admin_${Date.now()}_${Math.random().toString(36).substring(2, 7)}.${ext}`;
          const storageDir = getStorageDir();
          const targetPath = join(storageDir, safeFileName);
          writeFileSync(targetPath, buffer);
          const newImgUrl = `/images/products/${safeFileName}`;
          finalImages = [newImgUrl, ...finalImages.filter((img) => img !== newImgUrl)];
        } catch (imgErr) {
          console.error("[Action updateProduct] Image save error:", imgErr);
        }
      }

      const updateData: Record<string, any> = {
        name: name.trim(),
        description: description?.trim() || null,
        basePrice,
        category: category.trim(),
        slug: finalSlug,
        images: finalImages,
        updatedAt: new Date(),
      };

      if (stock !== undefined) {
        updateData.stock = stock;
        // Also synchronize variants
        await db.update(productVariants).set({ stock, price: basePrice }).where(eq(productVariants.productId, id));
      }

      await db
        .update(products)
        .set(updateData)
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
      stock: z.number().int().min(0).optional(),
      imageBase64: z.string().optional(),
      imageName: z.string().optional(),
    }),
    handler: async ({ name, description, basePrice, category, stock = 10, imageBase64, imageName }, context) => {
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
          stock,
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
        stock,
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

  // ==========================================
  // SERVICIOS DE MAQUILLAJE (ATELIER)
  // ==========================================
  toggleServiceStatus: defineAction({
    input: z.object({
      serviceId: z.string().uuid(),
      isActive: z.number().min(0).max(1),
    }),
    handler: async ({ serviceId, isActive }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Sesión no autenticada en /adminn." });
      }
      const db = getDb();
      const [serv] = await db.select().from(services).where(eq(services.id, serviceId)).limit(1);
      if (!serv) {
        throw new ActionError({ code: "NOT_FOUND", message: "Servicio no encontrado." });
      }
      await db.update(services).set({ isActive, updatedAt: new Date() }).where(eq(services.id, serviceId));
      notifySuperadminAudit(
        `💅 <b>Servicio /adminn</b>: <b>${serv.name}</b> ${isActive === 1 ? 'activado' : 'desactivado'} por <b>${adminUser.name}</b>.`
      ).catch(() => {});
      return { success: true, isActive };
    },
  }),

  updateService: defineAction({
    input: z.object({
      id: z.string().uuid(),
      name: z.string().min(1),
      description: z.string().optional(),
      price: z.number().positive(),
      durationMinutes: z.number().positive(),
      depositRequired: z.number().min(0).max(1),
      depositAmount: z.number().min(0),
      priceRange: z.string().optional(),
      badge: z.string().optional(),
      imageBase64: z.string().optional(),
      imageName: z.string().optional(),
    }),
    handler: async ({ id, name, description, price, durationMinutes, depositRequired, depositAmount, priceRange, badge, imageBase64, imageName }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Sesión no autenticada en /adminn." });
      }
      const db = getDb();
      const [current] = await db.select().from(services).where(eq(services.id, id)).limit(1);
      if (!current) {
        throw new ActionError({ code: "NOT_FOUND", message: "Servicio no encontrado." });
      }

      let finalImageUrl = current.imageUrl;
      if (imageBase64 && imageName) {
        try {
          const buffer = Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""), "base64");
          const ext = imageName.split(".").pop()?.toLowerCase() || "jpg";
          const safeFileName = `service_${Date.now()}_${Math.random().toString(36).substring(2, 7)}.${ext}`;
          const storageDir = getStorageDir();
          const targetPath = join(storageDir, safeFileName);
          writeFileSync(targetPath, buffer);
          finalImageUrl = `/images/products/${safeFileName}`;
        } catch (imgErr) {
          console.error("[Action updateService] Image save error:", imgErr);
        }
      }

      await db
        .update(services)
        .set({
          name: name.trim(),
          description: description?.trim() || null,
          price,
          durationMinutes,
          depositRequired,
          depositAmount,
          priceRange: priceRange?.trim() || null,
          badge: badge?.trim() || null,
          imageUrl: finalImageUrl,
          updatedAt: new Date(),
        })
        .where(eq(services.id, id));

      notifySuperadminAudit(
        `💅 <b>Servicio actualizado en /adminn</b>\nServicio: <b>${name}</b>\nPrecio: $${price.toLocaleString("es-CO")} COP\nModificado por: <b>${adminUser.name}</b>`
      ).catch(() => {});

      return { success: true };
    },
  }),

  createService: defineAction({
    input: z.object({
      name: z.string().min(1),
      description: z.string().optional(),
      price: z.number().positive(),
      durationMinutes: z.number().positive(),
      depositRequired: z.number().min(0).max(1),
      depositAmount: z.number().min(0),
      priceRange: z.string().optional(),
      badge: z.string().optional(),
      imageBase64: z.string().optional(),
      imageName: z.string().optional(),
    }),
    handler: async ({ name, description, price, durationMinutes, depositRequired, depositAmount, priceRange, badge, imageBase64, imageName }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Sesión no autenticada en /adminn." });
      }

      let baseSlug = name
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
      if (!baseSlug) baseSlug = `servicio-${Date.now()}`;

      let finalImageUrl = "/images/services/maquillaje-social-1.jpg";
      if (imageBase64 && imageName) {
        try {
          const buffer = Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""), "base64");
          const ext = imageName.split(".").pop()?.toLowerCase() || "jpg";
          const safeFileName = `service_${Date.now()}_${Math.random().toString(36).substring(2, 7)}.${ext}`;
          const storageDir = getStorageDir();
          const targetPath = join(storageDir, safeFileName);
          writeFileSync(targetPath, buffer);
          finalImageUrl = `/images/products/${safeFileName}`;
        } catch (imgErr) {
          console.error("[Action createService] Image save error:", imgErr);
        }
      }

      const db = getDb();
      const [newService] = await db
        .insert(services)
        .values({
          name: name.trim(),
          slug: baseSlug,
          description: description?.trim() || null,
          price,
          durationMinutes,
          depositRequired,
          depositAmount,
          priceRange: priceRange?.trim() || null,
          badge: badge?.trim() || null,
          imageUrl: finalImageUrl,
          isActive: 1,
        })
        .returning();

      notifySuperadminAudit(
        `✨ <b>Nuevo servicio creado en /adminn</b>\nServicio: <b>${newService.name}</b>\nSlug: <code>${newService.slug}</code>\nPrecio: $${price.toLocaleString("es-CO")} COP\nCreador: <b>${adminUser.name}</b>`
      ).catch(() => {});

      return { success: true, service: newService };
    },
  }),

  // ==========================================
  // CITAS & AGENDA (BOOKINGS)
  // ==========================================
  updateBookingStatus: defineAction({
    input: z.object({
      bookingId: z.string().uuid(),
      status: z.enum(["pending", "confirmed", "completed", "cancelled"]),
    }),
    handler: async ({ bookingId, status }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Sesión no autenticada en /adminn." });
      }
      const db = getDb();
      await db.update(bookings).set({ status }).where(eq(bookings.id, bookingId));
      return { success: true, status };
    },
  }),

  // ==========================================
  // CONFIGURACIÓN & PORTADA (SITE SETTINGS)
  // ==========================================
  updateSiteSetting: defineAction({
    input: z.object({
      key: z.string().min(1),
      value: z.record(z.any()),
      description: z.string().optional(),
    }),
    handler: async ({ key, value, description }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Sesión no autenticada en /adminn." });
      }
      const db = getDb();
      await db
        .insert(siteSettings)
        .values({
          key,
          value,
          description: description || null,
          updatedAt: new Date(),
        })
        .onConflictDoUpdate({
          target: siteSettings.key,
          set: {
            value,
            description: description || null,
            updatedAt: new Date(),
          },
        });
      return { success: true };
    },
  }),

  uploadBannerImage: defineAction({
    input: z.object({
      targetKey: z.enum(["hero_image", "hero_secondary_image"]),
      imageBase64: z.string().min(1),
      imageName: z.string().min(1),
      altText: z.string().optional(),
    }),
    handler: async ({ targetKey, imageBase64, imageName, altText }, context) => {
      const adminUser = context.locals.adminUser;
      if (!adminUser) {
        throw new ActionError({ code: "UNAUTHORIZED", message: "Sesión no autenticada en /adminn." });
      }
      const buffer = Buffer.from(imageBase64.replace(/^data:image\/\w+;base64,/, ""), "base64");
      const ext = imageName.split(".").pop()?.toLowerCase() || "jpg";
      const safeFileName = `banner_${Date.now()}_${Math.random().toString(36).substring(2, 7)}.${ext}`;
      const storageDir = getStorageDir();
      const targetPath = join(storageDir, safeFileName);
      writeFileSync(targetPath, buffer);
      const newImgUrl = `/images/products/${safeFileName}`;

      const db = getDb();
      const [curr] = await db.select().from(siteSettings).where(eq(siteSettings.key, targetKey)).limit(1);
      const currVal = (curr?.value as Record<string, any>) || {};
      const updatedVal = {
        ...currVal,
        url: newImgUrl,
        alt: altText || currVal.alt || "Banner portada",
      };

      await db
        .insert(siteSettings)
        .values({
          key: targetKey,
          value: updatedVal,
          updatedAt: new Date(),
        })
        .onConflictDoUpdate({
          target: siteSettings.key,
          set: {
            value: updatedVal,
            updatedAt: new Date(),
          },
        });

      return { success: true, url: newImgUrl };
    },
  }),
};
