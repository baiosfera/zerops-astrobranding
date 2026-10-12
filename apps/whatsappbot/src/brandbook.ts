import fs from "node:fs";
import path from "node:path";
import type { CustomerData, EventsContext } from "./db.js";

export interface BrandConfig {
  projectName: string;
  brandName: string;
  archetype: string;
  systemPrompt: string;
  canonicalUrls: Record<string, string>;
  rawBrandbook?: any;
}

export type CustomerHistoryContext = CustomerData;

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
  const projectName = process.env.PROJECT_NAME || process.env.APP_IDENTITY || "BRAND";
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

    // Check brandbook json candidates
    const jsonCandidates = [
      path.join(dir, `brandbook-${projectName.toLowerCase()}-potenciado.json`),
      path.join(dir, "brandbook.json"),
      path.join(dir, `brandbook-${projectName.toLowerCase()}.json`),
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

  const brandName =
    loadedJson?.brand_architecture?.umbrella_brand?.name ||
    loadedJson?.brand?.name ||
    process.env.BRAND_NAME ||
    projectName;

  const archetype =
    loadedJson?.brand_architecture?.leadership_and_ambassador?.brand_archetype ||
    loadedJson?.brand?.archetype ||
    process.env.BRAND_ARCHETYPE ||
    "Anfitrión Oficial y Concierge de Marca";

  const appBaseUrl =
    process.env.APP_URL ||
    process.env.CANONICAL_URL ||
    "http://localhost:3000";

  const canonicalUrls: Record<string, string> = {
    home: appBaseUrl,
    register: `${appBaseUrl}/#registro`,
    dashboard: `${appBaseUrl}/dashboard`,
    ...(loadedJson?.canonical_urls || {}),
  };

  return {
    projectName,
    brandName,
    archetype,
    systemPrompt: customMarkdownPrompt || "",
    canonicalUrls,
    rawBrandbook: loadedJson,
  };
}

function synthesizeAgnosticBrandPrompt(brand: BrandConfig): string {
  const json = brand.rawBrandbook || {};
  const umbrella = json.brand_architecture?.umbrella_brand || json.brand || {};
  const leadership = json.brand_architecture?.leadership_and_ambassador || json.leadership || {};
  const verbal = json.verbal_identity || json.voice_and_tone || {};
  const subBrands = json.brand_architecture?.sub_brands || json.sub_brands || {};
  const ethical = json.ethical_pillars_and_anti_bias || json.pillars || {};

  const hostName = leadership.name || "Equipo Oficial";
  const hostRole = leadership.role || "Anfitrión y Concierge";
  const brandName = umbrella.name || brand.brandName;
  const brandEssence = umbrella.essence || umbrella.description || "Servicio oficial";
  const brandTagline = umbrella.tagline || "";
  const brandMission = umbrella.mission || "";

  const toneDesc = verbal.tone || verbal.tone_of_voice || "Cercano, respetuoso, cálido, educado y resolutivo";
  const dialectDesc = verbal.dialect || verbal.speech_patterns || "Español natural, tuteo respetuoso, sin modismos extranjeros ni servicio meloso";

  let subBrandSection = "";
  if (typeof subBrands === "object" && subBrands !== null && Object.keys(subBrands).length > 0) {
    subBrandSection = "\n--- LÍNEAS / SUB-MARCAS / CATÁLOGO ---\n";
    for (const [key, val] of Object.entries(subBrands) as [string, any][]) {
      subBrandSection += `• ${val.name || key}: ${val.tagline || val.concept || ""}\n`;
      if (Array.isArray(val.hero_events || val.products || val.services)) {
        const items = (val.hero_events || val.products || val.services).join(", ");
        subBrandSection += `  Destacados: ${items}\n`;
      }
    }
  }

  let ethicalSection = "";
  if (typeof ethical === "object" && ethical !== null && Object.keys(ethical).length > 0) {
    ethicalSection = "\n--- PILARES ÉTICOS Y REGLAS DE MARCA ---\n";
    for (const [key, val] of Object.entries(ethical) as [string, any][]) {
      if (typeof val === "string") {
        ethicalSection += `• ${key}: ${val}\n`;
      } else if (typeof val === "object" && val !== null) {
        for (const [subKey, subVal] of Object.entries(val)) {
          ethicalSection += `• ${subKey}: ${subVal}\n`;
        }
      }
    }
  }

  let urlsSection = "\n--- ENLACES OFICIALES DISPONIBLES ---\n";
  for (const [key, val] of Object.entries(brand.canonicalUrls)) {
    urlsSection += `• ${key}: ${val}\n`;
  }

  return `Eres la voz oficial de ${hostName} (${hostRole}) de '${brandName}'.
Arquetipo: ${brand.archetype}.
Esencia de marca: ${brandEssence}.
${brandTagline ? `Lema: "${brandTagline}".` : ""}
${brandMission ? `Misión: ${brandMission}` : ""}

--- IDENTIDAD VOCAL Y TONO ---
• Tono de comunicación: ${toneDesc}.
• Pautas de lenguaje: ${dialectDesc}.
• ANTI-MELOSIDAD: Trata de adulto a adulto con respeto y calidez. Cero apelativos melosos ("mi amor", "mi vida", "dulzura", "bebé", "reina").
${subBrandSection}
${ethicalSection}
${urlsSection}
--- REGLAS DE CONVERSACIÓN ---
1. NATURALIDAD Y FLUIDEZ: Habla como miembro genuino del equipo, no como un robot genérico ni como un telemercaderista meloso.
2. CONTEXTO HISTÓRICO: Si la ficha del cliente muestra compras pasadas o condición VIP activa, reconócelo naturalmente. Si no está registrado, acógelo e invítalo a registrarse en el enlace oficial.
3. CONTINUIDAD: Entra directo a resolver sin repetir bienvenidas acartonadas si ya hay conversación previa.
4. HONESTIDAD: NUNCA inventes enlaces ni precios fuera de los datos oficiales.`;
}

export function buildSystemPrompt(
  customer?: CustomerHistoryContext,
  eventsContext?: EventsContext
): string {
  const brand = resolveBrandSSoT();
  const timeInfo = getBogotaTimeInfo();

  let eventsSection = "";
  if (eventsContext?.upcomingEventsSummary) {
    eventsSection += eventsContext.upcomingEventsSummary;
  }
  if (eventsContext?.pastEventsSummary) {
    eventsSection += eventsContext.pastEventsSummary;
  }

  let customerSection = "";
  if (!customer?.isRegistered) {
    customerSection = `\n--- ESTADO DEL INTERLOCUTOR: USUARIO NUEVO / NO REGISTRADO ---
• Estado en base de datos: AÚN NO REGISTRADO en la plataforma oficial (no tiene alias ni perfil verificado).
• INSTRUCCIÓN CLAVE DE REGISTRO:
  - Trátalo como a un recién llegado a quien recibes con total calidez y hospitalidad.
  - Si pregunta "¿cómo me llamo?", quién es, o busca acceder a opciones privadas o beneficios: explícale amablemente que aún no tienes su nombre o perfil registrado en el sistema.
  - INVÍTALO SIEMPRE a registrarse de forma gratuita en la plataforma oficial:
    👉 Enlace de registro: ${brand.canonicalUrls.register || brand.canonicalUrls.home + "/#registro"}
  - Explícale el beneficio: al registrarse crea su perfil oficial y accede a las novedades y servicios de la marca.${customer?.hasAffiliatesProgram ? " Además activa de inmediato su panel de embajador con su propio enlace para compartir." : ""}\n`;
  } else {
    // Dynamic role/gender adaptation
    let roleDescription = "👤 PERFIL DE USUARIO. Tono cercano, neutral y respetuoso.";
    if (customer.role === "hombre_solo") {
      roleDescription = "👨 HOMBRE SOLO (Perfil individual masculino). Dirígete a él como hombre (masculino singular: 'Embajador', 'miembro', 'bienvenido', 'tú').";
    } else if (customer.role === "mujer_sola") {
      roleDescription = "👩 MUJER SOLA (Perfil individual femenino). Dirígete a ella como mujer (femenino singular: 'Embajadora', 'miembro', 'bienvenida', 'tú').";
    } else if (customer.role === "pareja") {
      roleDescription = "👫 PAREJA (Cuenta compartida de pareja). ¡REGLA ESTRICTA!: Dirígete a ellos como pareja en plural o reconociendo su vínculo ('ustedes', 'pareja', 'chicos', 'ambos', 'como pareja', 'Embajadores'). NUNCA asumas que hablas con una mujer sola o un hombre solo ni uses 'Embajadora' en femenino singular.";
    }

    let vipSection = "";
    if (customer.hasVipProgram) {
      vipSection = `• ESTATUS VIP (DISTINCIÓN ESTRICTA — CERO CONFUSIÓN):
  ${customer.isPaidVip
    ? `👑 VIP ACTIVO CON CREDENCIAL PAGA (Válido hasta: ${customer.vipUntil || "Activa"}). Tiene membresía anual cancelada con credencial sellada y beneficios preferenciales.`
    : customer.isPossibleVip
      ? `💎 PERFIL INTERESADO EN SERVICIOS VIP (Sin membresía paga activa aún). Mostró interés o reservó previamente, pero NO TIENE CREDENCIAL PAGA ACTIVA. NUNCA le digas que ya tiene la credencial activa ni le atribuyas estatus VIP pago.`
      : `Estándar (Sin membresía VIP activa).`
  }\n`;
    }

    let affiliateSection = "";
    if (customer.hasAffiliatesProgram) {
      affiliateSection = `• PROGRAMA DE EMBAJADORES Y REFERIDOS:
  ${customer.affiliateAlias
    ? `⭐ ES EMBAJADOR ACTIVO:
       - Su alias / slug de embajador para compartir: ${customer.affiliateAlias}
       - Su enlace personal para compartir: ${customer.affiliateShareUrl || `${brand.canonicalUrls.home}/?ref=${customer.affiliateAlias}`}
       - Clics acumulados en su enlace: ${customer.affiliateClicks || 0}
       - Compras / Pases acreditados de sus referidos: ${customer.affiliatePaidReferrals || 0}
       - Entradas libres ganadas: ${customer.affiliateFreeTicketsEarned || 0}
       - Su panel privado: ${brand.canonicalUrls.dashboard || brand.canonicalUrls.home}
       INSTRUCCIÓN: Si pregunta por su enlace de referido, clics, pases o compras ganadas, entrégale sus cifras exactas y su link personal.`
    : `Aún no tiene alias de embajador activado. Indícale que puede activar su panel y obtener su enlace en ${brand.canonicalUrls.dashboard || brand.canonicalUrls.home}.`
  }\n`;
    }

    customerSection = `\n--- FICHA HISTÓRICA DEL MIEMBRO REGISTRADO (POSTGRESQL SSOT EN TIEMPO REAL) ---
• Nombre / Alias oficial ACTUAL: ${customer.alias || "Miembro registrado"}
• Teléfono: ${customer.phone || "Registrado"}
• Correo electrónico: ${customer.email || "No registrado"}
• Ciudad: ${customer.city || "No especificada"}
• TIPO DE PERFIL / ROL (${customer.role || "No especificado"}):
  ${roleDescription}
${vipSection}• Historial de asistencias/compras: ${customer.pastTickets && customer.pastTickets.length > 0
  ? customer.pastTickets.map(t => `- ${t.evento} (${t.tipo_entrada}) | Estado: ${t.estado} | Pagado: $${t.monto_pagado} | Fecha: ${t.fecha}`).join("\n")
  : "Sin compras registradas aún."}
${affiliateSection}
--- REGLA DE VERDAD ABSOLUTA EN TIEMPO REAL (SSOT > HISTORIAL) ---
1. Los datos de la FICHA DEL CLIENTE que acabas de leer provienen de PostgreSQL en este milisegundo exacto y son la VERDAD ABSOLUTA.
2. Si en los mensajes anteriores de la conversación usabas otro nombre, alias o rol (porque el usuario lo acaba de cambiar o por error previo), IGNORA el nombre o rol del historial antiguo.
3. Si el usuario menciona que cambió su nombre, rol, enlace o cualquier dato, o te pregunta si ya lo ves: CONFÍRMALE INMEDIATAMENTE su nombre y rol actuales según la ficha oficial (ej: "¡Totalmente! Ya veo en el sistema que tu nombre es ${customer.alias || "tu nuevo nombre"} y que están registrados como ${customer.role || "pareja"}..."). NUNCA digas que tarda minutos en sincronizarse ni te contradigas con la ficha.\n`;
  }

  // Base identity prompt (prefers markdown from SSoT if available, or synthesized from brandbook)
  const basePrompt = brand.systemPrompt || synthesizeAgnosticBrandPrompt(brand);
  const venueLine = brand.canonicalUrls.venue || (brand.rawBrandbook?.brand?.venue ? `\n• Sede Física Oficial: ${brand.rawBrandbook.brand.venue}` : "");

  return `${basePrompt}

--- TIEMPO PRESENTE CONTINUO (UTC-5) ---
• Momento actual: ${timeInfo.readableText}.
• Fecha ISO de referencia: ${timeInfo.isoDate}.${venueLine}
${eventsSection}${customerSection}`;
}

export function sanitizeAndValidateUrls(text: string): string {
  const brand = resolveBrandSSoT();
  const canonicalHost = new URL(brand.canonicalUrls.home || "http://localhost:3000").hostname;

  return text.replace(/https?:\/\/[^\s]+/g, (url) => {
    try {
      const parsed = new URL(url);
      if (parsed.hostname.includes(canonicalHost)) {
        return url;
      }
      if (parsed.hostname.includes("wa.me") || parsed.hostname.includes("x.com")) {
        return url;
      }
      return brand.canonicalUrls.home;
    } catch {
      return brand.canonicalUrls.home;
    }
  });
}

export function sanitizeTone(text: string): string {
  let cleaned = text.replace(/\banfitrionas?\b/gi, "facilitadoras y curadores");
  // Filter out any leaked pet names / mushy terms
  cleaned = cleaned.replace(/,\s*(?:mi amor|mi vida|dulzura|corazón|cielo|bebé|reina|princesa)\b/gi, "");
  cleaned = cleaned.replace(/\b(?:mi amor|mi vida|dulzura|corazón|cielo|bebé|reina|princesa)[,!]?\s*/gi, "");
  // Filter out Mexicanisms
  cleaned = cleaned.replace(/\b¡?Vaya!?,?\s*/gi, "");
  cleaned = cleaned.replace(/\bplaticar\b/gi, "hablar");
  cleaned = cleaned.replace(/\bplatica\b/gi, "charla");
  cleaned = cleaned.replace(/\bcharlar un rato\b/gi, "conversar");
  return cleaned;
}
