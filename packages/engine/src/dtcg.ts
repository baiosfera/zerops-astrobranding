/**
 * W3C Design Tokens Community Group (DTCG) Brandbook Engine
 * SSoT generator and S3 Object Storage bridge for Brandview and Astro-Web
 */

export interface DtcgToken<T = string | number> {
  $value: T;
  $type: "color" | "fontFamily" | "fontWeight" | "dimension" | "duration" | "shadow";
  $description?: string;
}

export interface DtcgBrandbook {
  $name: string;
  $version: string;
  color: {
    primary: DtcgToken<string>;
    secondary: DtcgToken<string>;
    accent: DtcgToken<string>;
    background: DtcgToken<string>;
    surface: DtcgToken<string>;
    text: DtcgToken<string>;
  };
  typography: {
    fontPrimary: DtcgToken<string>;
    fontSecondary: DtcgToken<string>;
    fontSizeBase: DtcgToken<string>;
    fontWeightBold: DtcgToken<number>;
  };
  metadata: {
    clientId?: string;
    generatedAt: string;
    generator: string;
    sourceShard?: string;
  };
}

/**
 * Builds a standard W3C DTCG compliant brandbook manifest
 */
export function buildDtcgBrandbook(params: {
  brandName: string;
  primaryColor?: string;
  accentColor?: string;
  backgroundColor?: string;
  fontPrimary?: string;
  fontSecondary?: string;
  clientId?: string;
  sourceShard?: string;
}): DtcgBrandbook {
  return {
    $name: params.brandName,
    $version: "1.0.0",
    color: {
      primary: {
        $value: params.primaryColor || "#f59e0b",
        $type: "color",
        $description: "Brand Primary Identity Color",
      },
      secondary: {
        $value: "#022c22",
        $type: "color",
        $description: "Brand Secondary Anchor Color",
      },
      accent: {
        $value: params.accentColor || "#10b981",
        $type: "color",
        $description: "Brand Dynamic Accent Color",
      },
      background: {
        $value: params.backgroundColor || "#09090b",
        $type: "color",
        $description: "Root Background Surface",
      },
      surface: {
        $value: "#171717",
        $type: "color",
        $description: "Elevated Surface and Cards",
      },
      text: {
        $value: "#f8fafc",
        $type: "color",
        $description: "High Contrast Body Text",
      },
    },
    typography: {
      fontPrimary: {
        $value: params.fontPrimary || "Cinzel, serif",
        $type: "fontFamily",
        $description: "Display and Heading Typography",
      },
      fontSecondary: {
        $value: params.fontSecondary || "Inter, sans-serif",
        $type: "fontFamily",
        $description: "Body and UI Typography",
      },
      fontSizeBase: {
        $value: "16px",
        $type: "dimension",
      },
      fontWeightBold: {
        $value: 700,
        $type: "fontWeight",
      },
    },
    metadata: {
      clientId: params.clientId,
      generatedAt: new Date().toISOString(),
      generator: "@astrobranding/engine v1.0",
      sourceShard: params.sourceShard || "default",
    },
  };
}

/**
 * Persists the brandbook.json to S3 Object Storage
 */
export async function uploadBrandbookToS3(
  brandbook: DtcgBrandbook,
  options?: { key?: string; s3Endpoint?: string; bucket?: string }
): Promise<{ success: boolean; s3Key: string; url?: string }> {
  const s3Key = options?.key || `brandbooks/${brandbook.metadata.clientId || "default"}/brandbook.json`;
  const content = JSON.stringify(brandbook, null, 2);

  const endpoint = options?.s3Endpoint || process.env.OBJECTSTORAGE_ENDPOINT;
  const bucket = options?.bucket || process.env.OBJECTSTORAGE_BUCKET || "brandview";

  if (!endpoint) {
    console.info(`[DTCG Bridge] Object Storage not configured. Brandbook manifest compiled in memory for key: ${s3Key}`);
    return { success: true, s3Key, url: `memory://${s3Key}` };
  }

  try {
    const uploadUrl = `${endpoint.replace(/\/$/, "")}/${bucket}/${s3Key}`;
    const res = await fetch(uploadUrl, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: content,
    });

    if (res.ok) {
      console.log(`[DTCG Bridge] Brandbook deployed successfully to S3: ${uploadUrl}`);
      return { success: true, s3Key, url: uploadUrl };
    }

    console.warn(`[DTCG Bridge] S3 upload returned ${res.status}. Falling back to memory response.`);
    return { success: false, s3Key };
  } catch (err) {
    console.warn(`[DTCG Bridge] S3 upload failed (${String(err)}). Local payload preserved.`);
    return { success: false, s3Key };
  }
}
