import { createHash, createHmac } from "node:crypto";
import type {
  MetaServerEventInput,
  MetaCapiResponse,
  MetaUserData,
} from "@astrobranding/contracts";

export interface MetaCapiConfig {
  pixelId?: string;
  accessToken?: string;
  appSecret?: string;
  testEventCode?: string;
  timeoutMs?: number;
  graphApiVersion?: string;
}

export interface MetaDispatchResult {
  success: boolean;
  eventId: string;
  data?: MetaCapiResponse;
  error?: string;
  statusCode?: number;
}

/**
 * SHA-256 hash helper complying with Meta's strict hashing requirements
 */
export function hashMetaField(value?: string | null): string | undefined {
  if (!value) return undefined;
  const clean = value.trim();
  if (!clean) return undefined;
  return createHash("sha256").update(clean).digest("hex");
}

/**
 * Normalizes email: trim and lowercase before hashing
 */
export function hashMetaEmail(email?: string | null): string | undefined {
  if (!email) return undefined;
  const clean = email.trim().toLowerCase();
  return hashMetaField(clean);
}

/**
 * Normalizes phone number: digits only, applies E.164 without '+'
 */
export function hashMetaPhone(phone?: string | null, defaultCountryCode = "57"): string | undefined {
  if (!phone) return undefined;
  let digits = phone.replace(/\D/g, "");
  if (!digits) return undefined;

  // Auto-prepend country code if national 10-digit mobile (e.g. Colombia mobile 3001234567)
  if (digits.length === 10 && digits.startsWith("3") && defaultCountryCode === "57") {
    digits = `57${digits}`;
  }

  return hashMetaField(digits);
}

/**
 * Generates an invariant Shared Event ID shared by Browser Pixel & Server CAPI
 */
export function generateMetaSharedEventId(prefix?: string): string {
  const p = prefix || process.env.PROJECT_PREFIX || "evt";
  const timestamp = Date.now();
  const random = crypto.randomUUID().slice(0, 8);
  return `${p}-${timestamp}-${random}`;
}

/**
 * Normalizes user data block into Meta CAPI format
 */
export function prepareMetaUserData(userData: MetaUserData) {
  const payload: Record<string, unknown> = {};

  if (userData.email) {
    payload.em = [hashMetaEmail(userData.email)];
  }
  if (userData.phone) {
    payload.ph = [hashMetaPhone(userData.phone)];
  }
  if (userData.firstName) {
    payload.fn = [hashMetaField(userData.firstName.toLowerCase())];
  }
  if (userData.lastName) {
    payload.ln = [hashMetaField(userData.lastName.toLowerCase())];
  }
  if (userData.city) {
    payload.ct = [hashMetaField(userData.city.toLowerCase().replace(/[^a-z]/g, ""))];
  }
  if (userData.state) {
    payload.st = [hashMetaField(userData.state.toLowerCase())];
  }
  if (userData.zip) {
    payload.zp = [hashMetaField(userData.zip.toLowerCase().replace(/[\s-]/g, ""))];
  }
  if (userData.country) {
    payload.country = [hashMetaField(userData.country.toLowerCase())];
  }
  if (userData.externalId) {
    payload.external_id = [hashMetaField(userData.externalId)];
  }

  // Cookies and network data MUST NOT be hashed
  if (userData.clientIp) {
    payload.client_ip_address = userData.clientIp;
  }
  if (userData.userAgent) {
    payload.client_user_agent = userData.userAgent;
  }
  if (userData.fbp) {
    payload.fbp = userData.fbp;
  }
  if (userData.fbc) {
    payload.fbc = userData.fbc;
  }

  return payload;
}

/**
 * Dispatches a server event to Meta Conversions API (CAPI) v21+
 * Agnóstico, desacoplado y protegido con timeout de 3 segundos
 */
export async function dispatchMetaSignal(
  event: MetaServerEventInput,
  config?: MetaCapiConfig
): Promise<MetaDispatchResult> {
  const pixelId =
    config?.pixelId ||
    process.env.META_PIXEL_ID;

  const accessToken =
    config?.accessToken ||
    process.env.META_CAPI_TOKEN ||
    process.env.META_CAPI_ACCESS_TOKEN;

  const testEventCode =
    config?.testEventCode ||
    process.env.META_TEST_EVENT_CODE;

  const apiVersion = config?.graphApiVersion || "v21.0";
  const timeoutMs = config?.timeoutMs || 3000;
  const eventId = event.eventId || generateMetaSharedEventId();

  if (!pixelId || !accessToken) {
    return {
      success: false,
      eventId,
      error: "Missing required Meta credentials: META_PIXEL_ID or META_CAPI_TOKEN is unset.",
    };
  }

  const normalizedUserData = prepareMetaUserData(event.userData);

  const eventPayload: Record<string, unknown> = {
    event_name: event.eventName,
    event_time: event.eventTime || Math.floor(Date.now() / 1000),
    event_id: eventId,
    action_source: event.actionSource || "website",
    user_data: normalizedUserData,
  };

  if (event.eventSourceUrl) {
    eventPayload.event_source_url = event.eventSourceUrl;
  }

  if (event.customData) {
    eventPayload.custom_data = event.customData;
  }

  const requestBody: Record<string, unknown> = {
    data: [eventPayload],
  };

  if (testEventCode) {
    requestBody.test_event_code = testEventCode;
  }

  const appSecret = config?.appSecret || process.env.META_APP_SECRET;
  let endpoint = `https://graph.facebook.com/${apiVersion}/${pixelId}/events`;
  if (appSecret) {
    const proof = createHmac("sha256", appSecret).update(accessToken).digest("hex");
    endpoint = `${endpoint}?appsecret_proof=${proof}`;
  }

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal,
    });

    clearTimeout(timer);

    const result = (await response.json()) as MetaCapiResponse;

    if (!response.ok || result.error) {
      return {
        success: false,
        eventId,
        statusCode: response.status,
        error: result.error?.message || `Meta API HTTP ${response.status}`,
        data: result,
      };
    }

    return {
      success: true,
      eventId,
      statusCode: response.status,
      data: result,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      eventId,
      error: `Meta CAPI dispatch error: ${message}`,
    };
  }
}
