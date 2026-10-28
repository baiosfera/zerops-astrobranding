import { z } from "zod";

/**
 * Supported Catalog Vertical Types in Meta Commerce & Platform
 */
export const MetaCatalogVerticalSchema = z.enum([
  "commerce",
  "services",
  "home_listings",
  "hotels",
  "vehicles",
  "generic",
]);

export type MetaCatalogVertical = z.infer<typeof MetaCatalogVerticalSchema>;

/**
 * Universal Catalog Item Schema (Zod)
 * Validates commerce products, services, bookings, and digital assets
 */
export const MetaCatalogItemSchema = z.object({
  id: z.string().min(1, "Item ID is required"),
  title: z.string().min(1, "Title is required"),
  description: z.string().min(1, "Description is required"),
  availability: z.enum([
    "in stock",
    "out of stock",
    "preorder",
    "available for order",
  ]).default("in stock"),
  condition: z.enum(["new", "refurbished", "used"]).default("new"),
  price: z.string().regex(/^\d+(\.\d{1,2})?\s+[A-Z]{3}$/, {
    message: "Price must follow format 'AMOUNT CURRENCY' (e.g. '120000.00 COP' or '85000 COP')",
  }),
  sale_price: z.string().regex(/^\d+(\.\d{1,2})?\s+[A-Z]{3}$/).optional(),
  link: z.string().url("Link must be a valid URL"),
  image_link: z.string().url("Image link must be a valid URL"),
  additional_image_link: z.array(z.string().url()).optional(),
  brand: z.string().min(1, "Brand is required"),
  item_group_id: z.string().optional(),
  color: z.string().optional(),
  size: z.string().optional(),
  gender: z.enum(["female", "male", "unisex"]).optional(),
  age_group: z.enum(["adult", "all ages", "teen", "kids", "toddler", "infant"]).optional(),
  material: z.string().optional(),
  pattern: z.string().optional(),
  custom_label_0: z.string().optional(),
  custom_label_1: z.string().optional(),
  custom_label_2: z.string().optional(),
  custom_label_3: z.string().optional(),
  custom_label_4: z.string().optional(),
  vertical: MetaCatalogVerticalSchema.default("commerce"),
  service_type: z.string().optional(),
  address: z.string().optional(),
  inventory: z.number().int().nonnegative().optional(),
});

export type MetaCatalogItem = z.infer<typeof MetaCatalogItemSchema>;

/**
 * Channel Metadata for RSS 2.0 / Google Merchant Feed Header
 */
export const MetaCatalogChannelMetadataSchema = z.object({
  title: z.string().min(1),
  link: z.string().url(),
  description: z.string().min(1),
  brand: z.string().optional(),
});

export type MetaCatalogChannelMetadata = z.infer<typeof MetaCatalogChannelMetadataSchema>;

/**
 * Meta Items Batch API Request Item (SOTA Realtime Catalog Push)
 */
export const MetaBatchMethodSchema = z.enum(["CREATE", "UPDATE", "DELETE"]);
export type MetaBatchMethod = z.infer<typeof MetaBatchMethodSchema>;

export const MetaCatalogBatchRequestItemSchema = z.object({
  method: MetaBatchMethodSchema,
  data: z.record(z.unknown()),
});

export type MetaCatalogBatchRequestItem = z.infer<typeof MetaCatalogBatchRequestItemSchema>;

export const MetaCatalogBatchPayloadSchema = z.object({
  item_type: z.enum(["PRODUCT_ITEM", "SERVICE_ITEM", "HOME_LISTING", "HOTEL", "VEHICLE"]).default("PRODUCT_ITEM"),
  requests: z.array(MetaCatalogBatchRequestItemSchema).min(1).max(5000),
});

export type MetaCatalogBatchPayload = z.infer<typeof MetaCatalogBatchPayloadSchema>;
