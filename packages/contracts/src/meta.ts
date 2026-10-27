import { z } from "zod";

export const MetaUserDataSchema = z.object({
  email: z.string().email().optional(),
  phone: z.string().optional(),
  clientIp: z.string().optional(),
  userAgent: z.string().optional(),
  fbp: z.string().optional(),
  fbc: z.string().optional(),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  zip: z.string().optional(),
  country: z.string().optional(),
  externalId: z.string().optional(),
});

export type MetaUserData = z.infer<typeof MetaUserDataSchema>;

export const MetaCustomContentItemSchema = z.object({
  id: z.string(),
  quantity: z.number().int().positive().default(1),
  item_price: z.number().optional(),
  title: z.string().optional(),
  category: z.string().optional(),
});

export type MetaCustomContentItem = z.infer<typeof MetaCustomContentItemSchema>;

export const MetaCustomDataSchema = z.object({
  value: z.number().optional(),
  currency: z.string().length(3).default("COP"),
  content_name: z.string().optional(),
  content_category: z.string().optional(),
  content_ids: z.array(z.string()).optional(),
  contents: z.array(MetaCustomContentItemSchema).optional(),
  num_items: z.number().int().optional(),
  order_id: z.string().optional(),
  status: z.string().optional(),
});

export type MetaCustomData = z.infer<typeof MetaCustomDataSchema>;

export const MetaStandardEventNameSchema = z.enum([
  "PageView",
  "ViewContent",
  "Search",
  "AddToCart",
  "AddToWishlist",
  "InitiateCheckout",
  "AddPaymentInfo",
  "Purchase",
  "Lead",
  "CompleteRegistration",
  "Contact",
  "CustomizeProduct",
  "Donate",
  "FindLocation",
  "Schedule",
  "StartTrial",
  "SubmitApplication",
  "Subscribe",
]);

export type MetaStandardEventName = z.infer<typeof MetaStandardEventNameSchema>;

export const MetaServerEventInputSchema = z.object({
  eventName: z.union([MetaStandardEventNameSchema, z.string()]),
  eventId: z.string(),
  eventTime: z.number().int().optional(),
  eventSourceUrl: z.string().url().optional(),
  actionSource: z.enum(["website", "app", "phone_call", "chat", "email", "other"]).default("website"),
  userData: MetaUserDataSchema.default({}),
  customData: MetaCustomDataSchema.optional(),
});

export type MetaServerEventInput = z.infer<typeof MetaServerEventInputSchema>;

export const MetaCapiResponseSchema = z.object({
  events_received: z.number().optional(),
  messages: z.array(z.string()).optional(),
  fbtrace_id: z.string().optional(),
  error: z.object({
    message: z.string(),
    type: z.string(),
    code: z.number(),
    error_subcode: z.number().optional(),
    fbtrace_id: z.string().optional(),
  }).optional(),
});

export type MetaCapiResponse = z.infer<typeof MetaCapiResponseSchema>;
