import type { APIRoute } from "astro";
import { getQueryClient } from "@astrobranding/database";
import { acquireCheckoutLock, buildWompiCheckoutData } from "../../../services/payments";
import { normalizeColombianPhone, sendCodOrderWhatsApp } from "../../../services/whatsapp";
import { sendOrderConfirmationEmail } from "../../../services/email";

export const prerender = false;

// Canonical Valle del Aburrá Sur municipalities eligible for COD (Envigado, Sabaneta, Itagüí, La Estrella)
export const VALLE_ABURRA_MUNICIPALITIES = [
  "envigado",
  "sabaneta",
  "itagui",
  "itagüí",
  "la estrella",
];

export function isValleAburra(city: string): boolean {
  if (!city) return false;
  const clean = city.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  return VALLE_ABURRA_MUNICIPALITIES.some((m) => {
    const cleanM = m.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return clean.includes(cleanM);
  });
}

// Backward compatibility alias
export const isValleAburraSur = isValleAburra;

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const {
      customerName,
      customerEmail,
      customerPhone,
      shippingAddress,
      shippingCity,
      shippingDepartment,
      daneCode,
      totalAmount,
      paymentMethod, // 'cod' | 'online'
      hasOrderBump = false,
      couponCode,
      items = [],
    } = body;

    if (!customerName || !customerPhone || !totalAmount) {
      return new Response(JSON.stringify({ error: "Faltan campos obligatorios (nombre, teléfono, total)" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Strict validation for Pago Contra Entrega (COD): ONLY Medellín and Valle del Aburrá + valid address
    if (paymentMethod === "cod") {
      if (!shippingAddress || shippingAddress.trim().length < 5) {
        return new Response(
          JSON.stringify({
            error: "Para Pago Contra Entrega es indispensable ingresar una dirección de entrega completa.",
          }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" },
          }
        );
      }

      if (!isValleAburra(shippingCity)) {
        return new Response(
          JSON.stringify({
            error: "El Pago Contra Entrega está disponible exclusivamente para el Valle del Aburrá Sur (Envigado, Sabaneta, Itagüí, La Estrella). Para otras ciudades, por favor selecciona Pago Seguro en Línea.",
          }),
          {
            status: 400,
            headers: { "Content-Type": "application/json" },
          }
        );
      }
    }

    const host = request.headers.get("host") || "";
    const environment = process.env.APP_ENV || (host.includes("webdev") || host.includes("localhost") || host.includes("127.0.0.1") ? "development" : "production");

    const reference = `CG-${Date.now().toString().slice(-4)}-${Math.random().toString(36).substring(2, 5).toUpperCase()}`;
    const normalizedPhone = normalizeColombianPhone(customerPhone);

    // Acquire Valkey 60s idempotency lock
    const locked = await acquireCheckoutLock(reference, 60);
    if (!locked) {
      return new Response(JSON.stringify({ error: "Transacción en proceso, por favor espere." }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      });
    }

    let orderId = reference;

    try {
      const sql = getQueryClient();
      const [order] = await sql`
        INSERT INTO orders (
          customer_name,
          customer_email,
          customer_phone,
          shipping_address,
          shipping_city,
          shipping_department,
          dane_code,
          total_amount,
          currency,
          payment_method,
          payment_ref,
          status,
          environment,
          notes
        ) VALUES (
          ${customerName},
          ${customerEmail || ""},
          ${normalizedPhone},
          ${shippingAddress || ""},
          ${shippingCity || "Envigado"},
          ${shippingDepartment || "Antioquia"},
          ${daneCode || "05266000"},
          ${Math.round(totalAmount)},
          \x27COP\x27,
          ${paymentMethod || "online"},
          ${reference},
          ${paymentMethod === "cod" ? "pending_cod" : "draft_checkout"},
          ${environment},
          ${couponCode ? "Cupón: " + String(couponCode).trim().toUpperCase() : null}
        )
        RETURNING id;
      `;
      orderId = order.id;
      if (couponCode) {
        await sql`
          UPDATE coupons
          SET used_count = used_count + 1, updated_at = NOW()
          WHERE UPPER(code) = ${String(couponCode).trim().toUpperCase()};
        `.catch((e: any) => console.warn('[Coupon count warning]', e));
      }

      if (items.length > 0) {
        for (const item of items) {
          if (item.productId) {
            await sql`
              INSERT INTO order_items (order_id, product_id, variant_id, quantity, unit_price)
              VALUES (${orderId}, ${item.productId}, ${item.variantId || null}, ${item.quantity || 1}, ${item.unitPrice || 0});
            `;
          }
        }
      }
    } catch (dbErr) {
      console.warn("Database order insert warning (continuing with reference):", dbErr);
    }

    const formattedTotal = new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      maximumFractionDigits: 0,
    }).format(totalAmount);

    const itemsSummary = items.length > 0
      ? items.map((i: any) => `${i.quantity || 1}x ${i.productId || "Enterizo Escultor"}`).join(", ")
      : "Enterizo Escultor Blanco Studio";

    // Multimensajería Transaccional Soberana (WhatsApp & Email)
    if (paymentMethod === "cod") {
      sendCodOrderWhatsApp({
        customerName,
        reference,
        itemsSummary,
        formattedTotal,
        shippingAddress: shippingAddress || "Dirección de domicilio",
        shippingCity: shippingCity || "Envigado",
        phone: normalizedPhone,
      }).catch((e) => console.warn("[WhatsApp COD] notification skipped:", e));
    }

    if (paymentMethod === "cod" && customerEmail && customerEmail.includes("@")) {
      sendOrderConfirmationEmail({
        customerName,
        customerEmail,
        reference,
        itemsSummary,
        totalAmountCop: totalAmount,
        paymentMethod: paymentMethod || "online",
        shippingAddress: shippingAddress || "Dirección de entrega",
        shippingCity: shippingCity || "Valle del Aburrá",
      }).catch((e) => console.warn("[Email Order] notification skipped:", e));
    }

    if (paymentMethod === "cod") {
      return new Response(
        JSON.stringify({
          success: true,
          mode: "cod",
          orderId,
          reference,
          message: "Pedido contra entrega confirmado para Medellín y Valle del Aburrá.",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // Online payment: Build Wompi SHA-256 integrity signature and session parameters
    const proto = request.headers.get("x-forwarded-proto") || (host.includes("localhost") ? "http" : "https");
    const redirectUrl = `${proto}://${host}/checkout/confirmacion`;

    const wompiData = buildWompiCheckoutData({
      reference,
      totalAmountCop: totalAmount,
      redirectUrl,
    });

    return new Response(
      JSON.stringify({
        success: true,
        mode: "online",
        orderId,
        reference,
        wompiData,
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (err: any) {
    console.error("Order processing error:", err);
    return new Response(JSON.stringify({ error: err.message || "Error al procesar la orden" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
};
