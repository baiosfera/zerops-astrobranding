import type { APIRoute } from "astro";
import { getQueryClient } from "@astrobranding/database";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const rawCode = body.code || "";
    const orderTotal = Number(body.orderTotal) || 0;

    const cleanCode = String(rawCode).trim().toUpperCase();
    if (!cleanCode) {
      return new Response(
        JSON.stringify({ valid: false, message: "Por favor ingresa un código de cupón." }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const sql = getQueryClient();
    const [coupon] = await sql`
      SELECT id, code, description, discount_type, discount_value, min_order_amount, max_uses, used_count, expires_at, is_active
      FROM coupons
      WHERE UPPER(code) = ${cleanCode}
      LIMIT 1;
    `;

    if (!coupon) {
      return new Response(
        JSON.stringify({ valid: false, message: `El cupón '${cleanCode}' no existe.` }),
        { status: 404, headers: { "Content-Type": "application/json" } }
      );
    }

    if (coupon.is_active !== 1) {
      return new Response(
        JSON.stringify({ valid: false, message: `El cupón '${cleanCode}' ya no está activo.` }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    if (coupon.expires_at && new Date(coupon.expires_at) < new Date()) {
      return new Response(
        JSON.stringify({ valid: false, message: `El cupón '${cleanCode}' ha expirado.` }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    if (coupon.max_uses !== null && coupon.max_uses !== undefined && coupon.used_count >= coupon.max_uses) {
      return new Response(
        JSON.stringify({ valid: false, message: `El cupón '${cleanCode}' ha alcanzado su límite de usos.` }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const minAmount = Number(coupon.min_order_amount) || 0;
    if (minAmount > 0 && orderTotal < minAmount) {
      const formattedMin = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(minAmount);
      return new Response(
        JSON.stringify({
          valid: false,
          message: `El pedido mínimo para aplicar '${cleanCode}' es ${formattedMin}.`,
        }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    let discountAmount = 0;
    const discountVal = Number(coupon.discount_value) || 0;
    if (coupon.discount_type === "percentage") {
      discountAmount = Math.round((orderTotal * discountVal) / 100);
    } else {
      discountAmount = Math.min(orderTotal, discountVal);
    }

    const newTotal = Math.max(0, orderTotal - discountAmount);

    return new Response(
      JSON.stringify({
        valid: true,
        code: coupon.code,
        description: coupon.description,
        discountType: coupon.discount_type,
        discountValue: discountVal,
        discountAmount,
        newTotal,
        message: `¡Cupón '${coupon.code}' aplicado correctamente!`,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  } catch (err: any) {
    console.error("Coupon validation error:", err);
    return new Response(
      JSON.stringify({ valid: false, message: "Error al procesar el cupón." }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
};
