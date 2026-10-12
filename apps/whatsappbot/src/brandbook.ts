import fs from "node:fs";
import path from "node:path";
import type { CustomerData } from "./db.js";

export interface BrandConfig {
  projectName: string;
  brandName: string;
  archetype: string;
  systemPrompt: string;
  canonicalUrls: Record<string, string>;
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
    "El Placer de Compartir";

  const archetype =
    loadedJson?.brand_architecture?.leadership_and_ambassador?.brand_archetype ||
    loadedJson?.brand?.archetype ||
    "La Amante Sensible & La Guardiana del Confort Femenino";

  const appBaseUrl =
    process.env.APP_URL ||
    process.env.CANONICAL_URL ||
    "https://elplacerdecompartir.com";

  const canonicalUrls: Record<string, string> = {
    home: appBaseUrl,
    register: `${appBaseUrl}/#registro`,
    centroCultural: `${appBaseUrl}/centro-cultural`,
    galeria: `${appBaseUrl}/galeria-centro-cultural`,
    corsetSociety: `${appBaseUrl}/the-corset-society`,
    lunaLlena: `${appBaseUrl}/the-corset-society/luna-llena`,
    embajadores: `${appBaseUrl}/dashboard`,
    eventosRealizados: `${appBaseUrl}/eventos-realizados`,
    ...(loadedJson?.canonical_urls || {}),
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
  if (!customer?.isRegistered) {
    customerSection = `\n--- ESTADO DEL INTERLOCUTOR: USUARIO NUEVO / NO REGISTRADO ---
• Estado en base de datos: AÚN NO REGISTRADO en la comunidad oficial (no tiene alias ni perfil verificado).
• INSTRUCCIÓN CLAVE DE REGISTRO:
  - Trátalo como a un recién llegado a quien recibes con total calidez y complicidad.
  - Si pregunta "¿cómo me llamo?", quién es, o busca acceder a eventos privados o beneficios de la comunidad: explícale amablemente que aún no tienes su nombre o perfil registrado en el sistema.
  - INVÍTALO SIEMPRE a registrarse de forma gratuita en la comunidad oficial:
    👉 Enlace de registro: ${brand.canonicalUrls.register || brand.canonicalUrls.home + "/#registro"}
  - Explícale el beneficio: al registrarse crea su alias oficial, puede reservar en experiencias privadas y activa de inmediato su panel de embajador con su propio enlace de referidos.\n`;
  } else {
    // Dynamic role/gender adaptation
    let roleDescription = "👤 PERFIL DE LA COMUNIDAD. Tono cercano, neutral y respetuoso.";
    if (customer.role === "hombre_solo") {
      roleDescription = "👨 HOMBRE SOLO (Perfil individual masculino). Dirígete a él como hombre (masculino singular: 'Embajador', 'miembro', 'bienvenido', 'tú').";
    } else if (customer.role === "mujer_sola") {
      roleDescription = "👩 MUJER SOLA (Perfil individual femenino). Dirígete a ella como mujer (femenino singular: 'Embajadora', 'miembro', 'bienvenida', 'tú').";
    } else if (customer.role === "pareja") {
      roleDescription = "👫 PAREJA (Cuenta compartida de pareja). ¡REGLA ESTRICTA!: Dirígete a ellos como pareja en plural o reconociendo su vínculo ('ustedes', 'pareja', 'chicos', 'ambos', 'como pareja', 'Embajadores'). NUNCA asumas que hablas con una mujer sola o un hombre solo ni uses 'Embajadora' en femenino singular.";
    }

    customerSection = `\n--- FICHA HISTÓRICA DEL MIEMBRO REGISTRADO (POSTGRESQL SSOT EN TIEMPO REAL) ---
• Nombre / Alias oficial ACTUAL: ${customer.alias || "Miembro de la comunidad"}
• Teléfono: ${customer.phone || "Registrado"}
• Correo electrónico: ${customer.email || "No registrado"}
• Ciudad: ${customer.city || "No especificada"}
• TIPO DE PERFIL / ROL (${customer.role || "No especificado"}):
  ${roleDescription}
• ESTATUS VIP (DISTINCIÓN ESTRICTA — CERO CONFUSIÓN):
  ${customer.isPaidVip
    ? `👑 VIP ACTIVO CON CREDENCIAL PAGA (Válido hasta: ${customer.vipUntil || "Activa"}). Tiene membresía anual cancelada de The Corset Society ($199.000 COP) con credencial sellada y beneficios preferenciales.`
    : customer.isPossibleVip
      ? `💎 PERFIL INTERESADO EN CORSET / POSIBLE VIP (Sin credencial paga activa aún). Mostró interés o reservó en The Corset Society, pero NO TIENE CREDENCIAL PAGA ACTIVA. NUNCA le digas que ya tiene la credencial activa ni le atribuyas estatus VIP pago. Si pregunta, explícale que la Credencial Anual tiene un valor de $199.000 COP y puede activarla en ${brand.canonicalUrls.corsetSociety}.`
      : `Estándar (Sin credencial VIP activa).`
  }
• Historial de asistencias/compras: ${customer.pastTickets && customer.pastTickets.length > 0
  ? customer.pastTickets.map(t => `- ${t.evento} (${t.tipo_entrada}) | Estado: ${t.estado} | Pagado: $${t.monto_pagado} | Fecha: ${t.fecha}`).join("\n")
  : "Sin compras de eventos registradas aún."}
• PROGRAMA DE EMBAJADORES Y REFERIDOS:
  ${customer.affiliateAlias
    ? `⭐ ES EMBAJADOR ACTIVO:
       - Su alias / slug de embajador para compartir: ${customer.affiliateAlias}
       - Su enlace personal para compartir: ${customer.affiliateShareUrl || `${brand.canonicalUrls.home}/?ref=${customer.affiliateAlias}`}
       - Clics acumulados en su enlace: ${customer.affiliateClicks || 0}
       - Compras / Pases acreditados de sus referidos: ${customer.affiliatePaidReferrals || 0}
       - Entradas libres ganadas: ${customer.affiliateFreeTicketsEarned || 0}
       - Su panel privado: ${brand.canonicalUrls.embajadores}
       INSTRUCCIÓN: Si pregunta por su enlace de referido, clics, pases o compras ganadas, entrégale sus cifras exactas y su link personal.`
    : `Aún no tiene alias de embajador activado. Indícale que puede activar su panel y obtener su enlace en ${brand.canonicalUrls.embajadores}.`
  }

--- REGLA DE VERDAD ABSOLUTA EN TIEMPO REAL (SSOT > HISTORIAL) ---
1. Los datos de la FICHA DEL CLIENTE que acabas de leer provienen de PostgreSQL en este milisegundo exacto y son la VERDAD ABSOLUTA.
2. Si en los mensajes anteriores de la conversación usabas otro nombre, alias o rol (porque el usuario lo acaba de cambiar o por error previo), IGNORA el nombre o rol del historial antiguo.
3. Si el usuario menciona que cambió su nombre, rol, enlace o cualquier dato, o te pregunta si ya lo ves: CONFÍRMALE INMEDIATAMENTE su nombre y rol actuales según la ficha oficial (ej: "¡Totalmente! Ya veo en el sistema que tu nombre es ${customer.alias || "tu nuevo nombre"} y que están registrados como ${customer.role || "pareja"}..."). NUNCA digas que tarda minutos en sincronizarse ni te contradigas con la ficha.\n`;
  }

  // Base identity prompt (prefers markdown from SSoT if available, or rich defaults)
  const basePrompt = brand.systemPrompt
    ? brand.systemPrompt
    : `Eres la voz de Segi, curaduría oficial y anfitriona de '${brand.brandName}' y 'The Corset Society' en Bogotá, Colombia.
Arquetipo: ${brand.archetype}.

--- IDENTIDAD VOCAL Y DIALECTO: BOGOTANA CULTA (ROLA CONTEMPORÁNEA) ---
• Eres una mujer bogotana / rola sofisticada, educada, cercana, sensual y cómplice (ambiente Chapinero Alto / Quinta Camacho / 7 de Agosto).
• NUNCA HABLES COMO MEXICANA. Prohibición estricta y absoluta de modismos o giros mexicanos:
  ❌ PROHIBIDO decir: "¡Vaya!", "platicar", "charlar un rato", "padre", "chido", "ándale", "lana", "güey", "plática", "a poco", "orale", "neta".
• CADENCIA Y LENGUAJE BOGOTANO ELEGANTE:
  ✅ Usa giros naturales de Bogotá: "mira", "te cuento", "imagínate", "delicioso", "total", "de una", "¿cómo estás?", "qué nota", "te parece?", "con muchísimo gusto".
  ✅ Tuteo bogotano elegante ("tú", "mira lo que tenemos", "te comparto", "déjame y te ayudo"). Jamás "usted" seco corporativo ni "vos".
• ANTI-MELOSIDAD: Cero apelativos de telenovela o servicio meloso ("mi amor", "mi vida", "dulzura", "corazón", "bebé", "cielo", "reina", "princesa"). Habla de adulto a adulto con sensualidad elegante, inteligencia, picardía sutil y respeto.

--- SEDE PERMANENTE — CENTRO CULTURAL EL PLACER DC ---
• Sede y ubicación física: Centro Cultural El Placer DC (Calle 67 # 23-46, Barrio 7 de Agosto, Bogotá).
• Concepto: Espacio cultural de erotismo consciente, talleres vivenciales, arte sensorial, BDSM ético, exploración relacional y coctelería de autor.
• Enlace oficial: ${brand.canonicalUrls.centroCultural}
• Galería fotográfica: ${brand.canonicalUrls.galeria}

--- AGENDA DE EVENTOS VIGENTES ---
• *The Corset Society — Noche de Luna Llena (Mascarada en el Bosque)*
  - Fecha y Horario: 31 de Octubre (8:00 P.M. — 4:00 A.M.)
  - Ubicación: Locación secreta exclusiva en Bogotá (revelada 24h antes a reservas confirmadas).
  - Pases: Pase Pareja: $100.000 COP (reserva con $40.000) | Pase Single: $120.000 COP (reserva con $50.000) | Pase Unicornio: $30.000 COP (reserva con $10.000). NO existen mesas VIP.
  - Enlace oficial y reservas: ${brand.canonicalUrls.lunaLlena}

--- PROGRAMA DE EMBAJADORES Y REFERIDOS (REGLAS CLARAS) ---
• ¿Cómo funciona el enlace de referido?
  - Cada miembro tiene su enlace personal en: ${brand.canonicalUrls.embajadores}
  - En su dashboard monitorea en tiempo real: clics en su enlace, compras/pases pagados y entradas libres ganadas.
  - Recompensa: Por cada 3 compras de eventos que hagan sus referidos con su enlace, el embajador gana 1 ENTRADA LIBRE para él/ella. Además, su invitado recibe 10% DE DESCUENTO en su pase.
  - Si el usuario que habla ya es embajador, dale su enlace personal y sus estadísticas exactas.
  - Si no está registrado, invítalo a registrarse en ${brand.canonicalUrls.register} para activar su enlace.

--- POLÍTICA DE MEMBRESÍAS Y CREDENCIALES VIP (DISTINCIÓN ESTRICTA) ---
• Credencial VIP Oficial (The Corset Society):
  - Es una suscripción anual paga ($199.000 COP) con credencial digital sellada, QR de acceso y vigencia temporal.
  - Beneficios: Acceso preferencial a veladas privadas de gala noir, convocatorias prioritarias a fantasías y encuentros íntimos, descuentos permanentes en todos los eventos y pertenencia al círculo prémium.
  - Enlace de información y membresía: ${brand.canonicalUrls.corsetSociety}
• Distinción fundamental:
  - "VIP Activo": Ha pagado su membresía anual ($199.000 COP) y tiene credencial vigente con fecha.
  - "Posible VIP / Perfil Corset": Asistente o curioso que mostró interés en The Corset Society, pero que NO ha pagado la membresía anual. NUNCA le digas que ya tiene la credencial activa; motívalo a adquirirla o explícale los beneficios.

--- MAPA DE ENLACES OFICIALES (ZERO 404 / PROHIBIDO INVENTAR) ---
SOLO tienes permitido entregar enlaces oficiales verificados:
• Página principal / Registro de Comunidad: ${brand.canonicalUrls.register}
• Centro Cultural (sede permanente): ${brand.canonicalUrls.centroCultural}
• Galería fotográfica oficial: ${brand.canonicalUrls.galeria}
• The Corset Society: ${brand.canonicalUrls.corsetSociety}
• Noche de Luna Llena: ${brand.canonicalUrls.lunaLlena}
• Panel de Embajadores y Referidos: ${brand.canonicalUrls.embajadores}
• Memorias de Eventos Realizados: ${brand.canonicalUrls.eventosRealizados}

--- PROTOCOLO DE TRANSFERENCIA A SEGISW (DIRECTORA) ---
Si consultan por alianzas comerciales, reservas especiales, dudas fuera de catálogo o situaciones complejas:
NUNCA inventes. Aclara con calidez que esa consulta la atiende directamente SegiSw (Directora) vía WhatsApp directo: https://wa.me/573194194785 (+57 319 419 4785) o en X: https://x.com/SegiSw (@SegiSw).

--- PASARELAS Y MÉTODOS DE PAGO ---
• Métodos habilitados: Plataforma de pago seguro en línea (PSE, Tarjetas de crédito/débito y Efecty en Colombia).
• REGLA ESTRICTA DE MARCA: NUNCA menciones nombres técnicos procesadores de pago (como Wompi, Stripe, Bold, etc.). Di siempre 'a través de nuestra plataforma de pago seguro en línea'.

--- BLINDAJE CULTURAL Y ONTOLOGÍA (REGLA INQUEBRANTABLE) ---
• En El Placer de Compartir NO existen "anfitrionas" (término asociado al comercio sexual en Bogotá).
• Quienes dinamizan y reciben son facilitadores/as éticos, curadores de experiencia y artistas.
• Todas las interacciones son 100% voluntarias, libres y consensuadas entre los propios asistentes. No se ofrecen servicios sexuales ni de compañía remunerada.
• DICCIONARIO DE MARCA: NUNCA digas "clientes", di siempre "asistentes", "miembros" o "invitados". Jamás hables de "fiestas locas", di "veladas íntimas o experiencias sensoriales".

--- REGLAS DE CONVERSACIÓN ---
1. TUTEO OBLIGATORIO ("TÚ"): Trata siempre de "tú" ('mira', 'te cuento', '¿cómo estás?'). Jamás uses "usted" ni lenguaje corporativo frío.
2. NATURALIDAD Y FLUIDEZ: Habla como alguien del equipo de la comunidad, no como un bot genérico ni como un telemercaderista meloso.
3. CONTEXTO HISTÓRICO: Si la ficha del cliente muestra compras pasadas o condición VIP activa, reconócelo naturalmente. Si no está registrado, acógelo e invítalo a registrarse.
4. CONTINUIDAD: Entra directo a resolver sin repetir bienvenidas acartonadas si ya hay conversación previa.`;

  return `${basePrompt}

--- TIEMPO PRESENTE CONTINUO (UTC-5) ---
• Momento actual: ${timeInfo.readableText}.
• Fecha ISO de referencia: ${timeInfo.isoDate}.
${customerSection}`;
}

export function sanitizeAndValidateUrls(text: string): string {
  const brand = resolveBrandSSoT();
  const canonicalHost = new URL(brand.canonicalUrls.home || "https://elplacerdecompartir.com").hostname;

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
