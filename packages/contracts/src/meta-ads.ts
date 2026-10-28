import { z } from "zod";

export const MetaVideoUploadStartResponseSchema = z.object({
  video_id: z.string(),
  upload_session_id: z.string(),
  start_offset: z.string(),
  end_offset: z.string(),
});

export type MetaVideoUploadStartResponse = z.infer<typeof MetaVideoUploadStartResponseSchema>;

export const MetaVideoStatusResponseSchema = z.object({
  id: z.string(),
  status: z.object({
    video_status: z.string(),
    uploading_phase: z.object({
      status: z.string().optional(),
      bytes_transferred: z.number().optional(),
    }).optional(),
    processing_phase: z.object({
      status: z.string().optional(),
    }).optional(),
  }).optional(),
});

export type MetaVideoStatusResponse = z.infer<typeof MetaVideoStatusResponseSchema>;

export const MetaAdCreativeInputSchema = z.object({
  name: z.string().min(1),
  videoId: z.string().min(1),
  pageId: z.string().min(1),
  instagramActorId: z.string().optional(),
  title: z.string().optional(),
  body: z.string().min(1),
  link: z.string().url(),
  callToActionType: z.enum([
    "SHOP_NOW",
    "LEARN_MORE",
    "SIGN_UP",
    "BOOK_TRAVEL",
    "CONTACT_US",
    "ORDER_NOW"
  ]).default("SHOP_NOW"),
});

export type MetaAdCreativeInput = z.infer<typeof MetaAdCreativeInputSchema>;

export const MetaAdInputSchema = z.object({
  name: z.string().min(1),
  adsetId: z.string().min(1),
  creativeId: z.string().min(1),
  status: z.enum(["PAUSED", "ACTIVE"]).default("PAUSED"),
});

export type MetaAdInput = z.infer<typeof MetaAdInputSchema>;

export const MetaAdResultSchema = z.object({
  id: z.string(),
  success: z.boolean().default(true),
});

export type MetaAdResult = z.infer<typeof MetaAdResultSchema>;
