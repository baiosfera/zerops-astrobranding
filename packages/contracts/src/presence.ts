import { z } from "zod";

/**
 * Brand Presence Taxonomy: Defines whether a business has a physical store,
 * operates as a Service Area Business (SAB), or is purely digital/online.
 */
export const BrandPresenceModelSchema = z.enum([
  "physical_storefront",     // Walk-in retail store, beauty salon, or studio with public address
  "service_area_business",  // SAB: Mobile services, on-site appointments, no public physical walk-in
  "pure_online_national",   // Nationwide e-commerce / digital platform with shipping/online access
  "pure_online_global",     // Global SaaS, international digital offerings, worldwide courses
]);

export type BrandPresenceModel = z.infer<typeof BrandPresenceModelSchema>;

export const GeoCoordinatesSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
});

export type GeoCoordinates = z.infer<typeof GeoCoordinatesSchema>;

export const OpeningHoursSpecificationSchema = z.object({
  dayOfWeek: z.array(z.enum([
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ])),
  opens: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/, "HH:MM format required"),
  closes: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/, "HH:MM format required"),
});

export type OpeningHoursSpecification = z.infer<typeof OpeningHoursSpecificationSchema>;

export const BrandPresenceProfileSchema = z.object({
  presence_model: BrandPresenceModelSchema,
  business_name: z.string().min(1),
  legal_name: z.string().optional(),
  primary_telephone: z.string().optional(),
  primary_email: z.string().email().optional(),
  website_url: z.string().url(),
  schema_org_type: z.enum([
    "BeautySalon",
    "HealthAndBeautyBusiness",
    "Store",
    "ClothingStore",
    "ProfessionalService",
    "Organization",
    "OnlineStore",
  ]).default("Organization"),
  
  // Physical Storefront Attributes (Strictly required or validated for physical_storefront)
  google_maps_cid: z.string().optional(),
  has_map_url: z.string().url().optional(),
  street_address: z.string().optional(),
  locality: z.string().optional(), // City
  region: z.string().optional(),   // State/Department
  postal_code: z.string().optional(),
  country_code: z.string().length(2).default("CO"),
  geo: GeoCoordinatesSchema.optional(),
  opening_hours: z.array(OpeningHoursSpecificationSchema).default([]),

  // Service Area Business (SAB) Attributes (Hides residential address, defines service reach)
  service_areas: z.array(z.string()).default([]), // Cities or municipalities e.g. ["Envigado", "Sabaneta"]
  service_radius_meters: z.number().positive().optional(),

  // Disambiguation
  same_as_urls: z.array(z.string().url()).default([]),
});

export type BrandPresenceProfile = z.infer<typeof BrandPresenceProfileSchema>;
