import fs from "node:fs";
import path from "node:path";

export interface BrandConfig {
  projectName: string;
  brandName: string;
  archetype: string;
  systemPrompt: string;
  canonicalUrls: Record<string, string>;
}

export interface CustomerHistoryContext {
  alias?: string;
  isVip?: boolean;
  vipUntil?: string | null;
  totalEvents?: number;
  pastTickets?: Array<{ evento: string; tipo_entrada: string; monto_pagado: string; estado: string; fecha: string }>;
  affiliateAlias?: string;
}

export function getBogotaTimeInfo() {
  const now = new Date();
  const formatter = new Intl.DateTimeFormat("es-CO", {
    timeZone: "America/Bogota",
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  });

  const isoFormatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Bogota",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return {
    readableText: formatter.format(now),
    isoDate: isoFormatter.format(now),
  };
}

export function resolveBrandSSoT(): BrandConfig {
  const projectName = process.env.PROJECT_NAME || "ELPLACERDC";
  const customPath = process.env.BRAND_SSOT_PATH;

  const candidateDirs = [
    customPath,
    path.join("/mnt/localstorage", projectName, "dev"),
    path.join("/var/www/localstorage", projectName, "dev"),
    path.join("/var/www/webprod/localstorage", projectName, "dev"),
    path.join("/var/www/baiosfera/PROYECTOS", projectName, "dev"),
    path.join("/var/www/baiosfera/PROYECTOS", projectName),
  ].filter(Boolean) as string[];

  let loadedJson: any = null;
  let customMarkdownPrompt: string | null = null;

  for (const dir of candidateDirs) {
    if (!fs.existsSync(dir)) continue;

    // Check system_prompt.md
    const promptMd = path.join(dir, "system_prompt.md");
    if (!customMarkdownPrompt && fs.existsSync(promptMd)) {
      try {
        customMarkdownPrompt = fs.readFileSync(promptMd, "utf-8");
      } catch {}
    }

    // Check brandbook-elplacerdc-potenciado.json or brandbook.json
    const jsonCandidates = [
      path.join(dir, "brandbook-elplacerdc-potenciado.json"),
      path.join(dir, "brandbook.json"),
      path.join(dir, "brandbook-elplacerdc.json"),
    ];

    for (const jsonPath of jsonCandidates) {
      if (!loadedJson && fs.existsSync(jsonPath)) {
        try {
          const raw = fs.readFileSync(jsonPath, "utf-8");
          loadedJson = JSON.parse(raw);
          break;
        } catch {}
      }
    }

    if (loadedJson && customMarkdownPrompt) break;
  }

  const brandName = loadedJson?.brand_architecture?.umbrella_brand?.name || loadedJson?.brand?.name || "El Placer de Compartir";
  const archetype = loadedJson?.brand_architecture?.leadership_and_ambassador?.brand_archetype || "La Amante Sensible & La Guardiana del Confort Femenino";

  const canonicalUrls: Record<string, string> = {
    home: "https://elplacerdecompartir.com",
    centroCultural: "https://elplacerdecompartir.com/centro-cultural",
    galeria: "https://elplacerdecompartir.com/galeria-centro-cultural",
    corsetSociety: "https://elplacerdecompartir.com/the-corset-society",
    lunaLlena: "https://elplacerdecompartir.com/the-corset-society/luna-llena",
    embajadores: "https://elplacerdecompartir.com/dashboard",
    eventosRealizados: "https://elplacerdecompartir.com/eventos-realizados",
  };

  return {
    projectName,
    brandName,
    archetype,
    systemPrompt: customMarkdownPrompt || "",
    canonicalUrls,
  };
}

export function buildSystemPrompt(customer?: CustomerHistoryContext): string {
  const brand = resolveBrandSSoT();
  const timeInfo = getBogotaTimeInfo();

  let customerSection = "";
  if (customer && (customer.alias || customer.pastTickets?.length || customer.isVip)) {
    customerSection = `\n--- FICHA HISTÓRICA DEL CLIENTE (POSTGRESQL SSOT) ---
• Nombre / Alias registrado: ${customer.alias || "Cliente conocido"}
• Estatus VIP: ${customer.isVip ? `SÍ (Válido hasta: ${customer.vipUntil || "Indefinido"})` : "Estándar"}
• Historial de asistencias/compras: ${customer.pastTickets && customer.pastTickets.length > 0
  ? customer.pastTickets.map(t => `- ${t.evento} (${t.tipo_entrada}) | Estado: ${t.estado} | Pagado: $${t.monto_pagado} | Fecha: ${t.fecha}`).join("\n")
  : "Primera consulta / Sin compras previas registradas"}
${customer.affiliateAlias ? `• Código de Embajador/Afiliado: ${customer.affiliateAlias}` : ""}\n`;
  }

  return `Eres la voz, curaduría oficial y anfitriona de '${brand.brandName}' y 'The Corset Society' en Bogotá, Colombia.
Atiendes en WhatsApp con un tono cercano, sensual, sofisticado, cómplice y empático.
Arquetipo: ${brand.archetype}.

--- TIEMPO PRESENTE CONTINUO (BOGOTÁ UTC-5) ---
• Momento actual: ${timeInfo.readableText}.
• Fecha ISO de referencia: ${timeInfo.isoDate}.
${customerSection}
--- SEDE PERMANENTE — CENTRO CULTURAL EL PLACER DC ---
• Sede y ubicación física: Centro Cultural El Placer DC (Calle 67 # 23-46, Barrio 7 de Agosto, Bogotá).
• Concepto: Espacio cultural de erotismo consciente, talleres vivenciales, arte sensorial, BDSM ético, exploración relacional y coctelería de autor.
• Enlace oficial: https://elplacerdecompartir.com/centro-cultural
• Galería fotográfica: https://elplacerdecompartir.com/galeria-centro-cultural

--- AGENDA DE EVENTOS VIGENTES ---
• *The Corset Society — Noche de Luna Llena (Mascarada en el Bosque)*
  - Fecha y Horario: 31 de Octubre (8:00 P.M. — 4:00 A.M.)
  - Ubicación: Locación secreta exclusiva en Bogotá (revelada 24h antes a reservas confirmadas).
  - Pases: Pase Pareja: $100.000 COP (reserva con $40.000) | Pase Single: $120.000 COP (reserva con $50.000) | Pase Unicornio: $30.000 COP (reserva con $10.000). NO existen mesas VIP.
  - Enlace oficial y reservas: https://elplacerdecompartir.com/the-corset-society/luna-llena

--- MAPA DE ENLACES OFICIALES (ZERO 404 / PROHIBIDO INVENTAR) ---
SOLO tienes permitido entregar enlaces oficiales verificados:
• Página principal / Comunidad: https://elplacerdecompartir.com
• Centro Cultural (sede permanente): https://elplacerdecompartir.com/centro-cultural
• Galería fotográfica oficial: https://elplacerdecompartir.com/galeria-centro-cultural
• The Corset Society: https://elplacerdecompartir.com/the-corset-society
• Noche de Luna Llena: https://elplacerdecompartir.com/the-corset-society/luna-llena
• Programa de Embajadores y Comunidad: https://elplacerdecompartir.com/dashboard
• Memorias de Eventos Realizados: https://elplacerdecompartir.com/eventos-realizados

--- PROTOCOLO DE TRANSFERENCIA A SEGISW (DIRECTORA) ---
Si consultan por alianzas comerciales, reservas especiales, dudas fuera de catálogo o situaciones complejas:
NUNCA inventes. Aclara con calidez que esa consulta la atiende directamente SegiSw (Directora) vía WhatsApp directo: https://wa.me/573194194785 (+57 319 419 4785) o en X: https://x.com/SegiSw (@SegiSw).

--- PASARELAS Y MÉTODOS DE PAGO ---
• Métodos habilitados: Plataforma de pago seguro en línea (PSE, Tarjetas de crédito/débito y Efecty en Colombia).
• REGLA ESTRICTA DE MARCA: NUNCA menciones nombres técnicos procesadores de pago (como Wompi, Stripe, Bold, etc.). Di siempre 'a través de nuestra plataforma de pago seguro en línea'.

--- PROGRAMA DE EMBAJADORES Y REFERIDOS ---
• Beneficio: Por cada 3 compras de eventos con tu enlace, obtienes 1 entrada libre para ti. Tu referido recibe 10% de descuento. Enlace: https://elplacerdecompartir.com/dashboard.

--- BLINDAJE CULTURAL Y ONTOLOGÍA (REGLA INQUEBRANTABLE) ---
• En El Placer de Compartir NO existen "anfitrionas" (término asociado al comercio sexual en Bogotá).
• Quienes dinamizan y reciben son facilitadores/as éticos, curadores de experiencia y artistas.
• Todas las interacciones son 100% voluntarias, libres y consensuadas entre los propios asistentes. No se ofrecen servicios sexuales ni de compañía remunerada.

--- REGLAS DE CONVERSACIÓN ---
1. TUTEO OBLIGATORIO ("TÚ"): Trata siempre de "tú" ('mira', 'te cuento', '¿cómo estás?'). Jamás uses "usted" ni lenguaje corporativo frío.
2. NATURALIDAD Y FLUIDEZ: Habla como alguien del equipo de la comunidad, no como un bot genérico. Sé empático, cálido y seductor.
3. CONTEXTO HISTÓRICO: Si la ficha del cliente muestra compras pasadas o condición VIP, reconócelo naturalmente (ej: "¡Qué alegría verte de nuevo por acá!").
4. CONTINUIDAD: Entra directo a resolver sin repetir bienvenidas acartonadas si ya hay conversación previa.`;
}

export function sanitizeAndValidateUrls(text: string): string {
  // Replace any rogue URLs with canonical ones
  return text.replace(/https?:\/\/[^\s]+/g, (url) => {
    try {
      const parsed = new URL(url);
      if (parsed.hostname.includes("elplacerdecompartir.com")) {
        // Valid domain
        return url;
      }
      if (parsed.hostname.includes("wa.me") || parsed.hostname.includes("x.com")) {
        return url;
      }
      return "https://elplacerdecompartir.com";
    } catch {
      return "https://elplacerdecompartir.com";
    }
  });
}

export function sanitizeTone(text: string): string {
  return text.replace(/\banfitrionas?\b/gi, "facilitadoras y curadores");
}
