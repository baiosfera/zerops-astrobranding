import { z } from "zod";

/**
 * Offering Archetypes: 6 Commercial archetypes for any brand or project.
 */
export const OfferingArchetypeSchema = z.enum([
  "physical_goods",     // E-commerce items with inventory and shipping (apparel, cosmetics, gear)
  "courses_education",  // Workshops, masterclasses, cohorts, online video courses
  "memberships_mrr",    // Recurring subscriptions, VIP clubs, retainer services
  "events_ticketing",   // In-person or virtual ticketed events, summits, launches
  "digital_products",   // Downloadable files, ebooks, presets, digital licenses
  "service_bookings",   // 1-on-1 consultations, salon appointments, custom atelier services
]);

export type OfferingArchetype = z.infer<typeof OfferingArchetypeSchema>;

/**
 * Advertising Channel Strategy: Determines how each archetype is marketed
 * to comply with Meta Commerce Policy 19, Google Merchant Center, and TikTok Shopping.
 */
export const OfferingChannelStrategySchema = z.enum([
  "commerce_feed",          // Eligible for Meta Catalog, Google Merchant Center, TikTok Catalog (strictly physical_goods)
  "direct_web_conversion",  // Web landing conversion campaigns (courses, memberships, tickets, digital goods)
  "messaging_booking",      // WhatsApp/Direct lead qualification and appointment scheduling (services)
]);

export type OfferingChannelStrategy = z.infer<typeof OfferingChannelStrategySchema>;

export const OfferingSchema = z.object({
  id: z.string().uuid(),
  sku: z.string().min(1),
  title: z.string().min(1),
  description: z.string().min(1),
  archetype: OfferingArchetypeSchema,
  channel_strategy: OfferingChannelStrategySchema,
  price: z.number().nonnegative(),
  currency: z.string().length(3).default("COP"),
  availability: z.enum(["in_stock", "out_of_stock", "preorder", "backorder"]).default("in_stock"),
  condition: z.enum(["new", "refurbished", "used"]).default("new"),
  url: z.string().url(),
  image_url: z.string().url(),
  additional_image_urls: z.array(z.string().url()).default([]),
  brand: z.string().min(1),
  item_group_id: z.string().optional(),
  
  // Custom metadata tailored to specific archetype
  archetype_metadata: z.record(z.unknown()).default({}),
  
  is_active: z.boolean().default(true),
  created_at: z.date().default(() => new Date()),
  updated_at: z.date().default(() => new Date()),
});

export type Offering = z.infer<typeof OfferingSchema>;
