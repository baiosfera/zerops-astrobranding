import { z } from "zod";

/**
 * Google Consent Mode v2 Standards (2026)
 */
export const ConsentStatusSchema = z.enum(["granted", "denied"]);
export type ConsentStatus = z.infer<typeof ConsentStatusSchema>;

export const ConsentModeV2Schema = z.object({
  ad_storage: ConsentStatusSchema.default("denied"),
  ad_user_data: ConsentStatusSchema.default("denied"),
  ad_personalization: ConsentStatusSchema.default("denied"),
  analytics_storage: ConsentStatusSchema.default("denied"),
  wait_for_update: z.number().int().positive().default(500),
});

export type ConsentModeV2 = z.infer<typeof ConsentModeV2Schema>;

/**
 * 1st-Party Cookie Attribution Engine (90-day persistence)
 */
export const AttributionTouchSchema = z.object({
  timestamp: z.number().int().positive(),
  landing_url: z.string().url(),
  referrer: z.string().default(""),
  utm_source: z.string().optional(),
  utm_medium: z.string().optional(),
  utm_campaign: z.string().optional(),
  utm_term: z.string().optional(),
  utm_content: z.string().optional(),
  gclid: z.string().optional(),
  gbraid: z.string().optional(),
  wbraid: z.string().optional(),
  fbclid: z.string().optional(),
  ttclid: z.string().optional(),
  msclkid: z.string().optional(),
});

export type AttributionTouch = z.infer<typeof AttributionTouchSchema>;

export const AttributionSessionSchema = z.object({
  client_id: z.string().uuid(),
  fbp: z.string().optional(), // Format: fb.1.<ts>.<random>
  fbc: z.string().optional(), // Format: fb.1.<ts>.<fbclid>
  first_touch: AttributionTouchSchema,
  last_touch: AttributionTouchSchema,
});

export type AttributionSession = z.infer<typeof AttributionSessionSchema>;

/**
 * Commercial Signals: Unified multi-network event model (Meta CAPI + Google Ads + TikTok Events)
 */
export const CommercialSignalNameSchema = z.enum([
  "PageView",
  "ViewContent",
  "AddToCart",
  "InitiateCheckout",
  "AddPaymentInfo",
  "Purchase",
  "Subscribe",
  "Schedule",
  "Lead",
  "CompleteRegistration",
]);

export type CommercialSignalName = z.infer<typeof CommercialSignalNameSchema>;

export const CommercialUserDataSchema = z.object({
  email: z.string().email().optional(),
  phone: z.string().optional(), // E.164 normalized
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  client_ip_address: z.string().optional(),
  client_user_agent: z.string().optional(),
  fbp: z.string().optional(),
  fbc: z.string().optional(),
  external_id: z.string().optional(),
});

export type CommercialUserData = z.infer<typeof CommercialUserDataSchema>;

export const CommercialSignalSchema = z.object({
  event_id: z.string().min(1), // Shared idempotency key for browser and server deduplication
  event_name: CommercialSignalNameSchema,
  event_time: z.number().int().positive().default(() => Math.floor(Date.now() / 1000)),
  event_source_url: z.string().url(),
  action_source: z.enum(["website", "app", "system_generated"]).default("website"),
  content_type: z.enum(["product", "course", "membership", "service", "event", "digital"]).default("product"),
  value: z.number().nonnegative().optional(),
  currency: z.string().length(3).default("COP"),
  user_data: CommercialUserDataSchema,
  custom_data: z.record(z.unknown()).default({}),
  attribution: AttributionSessionSchema.optional(),
});

export type CommercialSignal = z.infer<typeof CommercialSignalSchema>;
