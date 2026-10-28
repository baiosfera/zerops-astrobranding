import { z } from "zod";

export const WhatsAppSendOtpSchema = z.object({
  phoneNumber: z.string().min(7),
  template: z.enum(["otp_verification", "welcome_dossier", "notification"]).default("otp_verification"),
  clientName: z.string().optional(),
  brandName: z.string().optional(),
});

export type WhatsAppSendOtpInput = z.infer<typeof WhatsAppSendOtpSchema>;

export const WhatsAppIncomingWebhookSchema = z.object({
  event: z.string(),
  instance: z.string(),
  data: z.object({
    key: z.object({
      remoteJid: z.string(),
      fromMe: z.boolean(),
      id: z.string(),
    }),
    message: z.record(z.unknown()).optional(),
    messageTimestamp: z.number().or(z.string()),
    pushName: z.string().optional(),
  }),
});

export type WhatsAppIncomingWebhook = z.infer<typeof WhatsAppIncomingWebhookSchema>;
