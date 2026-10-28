import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  MetaVideoUploadStartResponseSchema,
  MetaVideoStatusResponseSchema,
  MetaAdCreativeInputSchema,
  MetaAdInputSchema,
} from "@astrobranding/contracts";
import { MetaAdsClient } from "./meta-ads.ts";

describe("Meta Ads Engine & Contracts Suite", () => {
  it("MetaVideoUploadStartResponseSchema parses valid start payload", () => {
    const raw = {
      video_id: "vid_987654321",
      upload_session_id: "sess_abc123xyz",
      start_offset: "0",
      end_offset: "20971520",
    };
    const parsed = MetaVideoUploadStartResponseSchema.parse(raw);
    assert.equal(parsed.video_id, "vid_987654321");
    assert.equal(parsed.upload_session_id, "sess_abc123xyz");
  });

  it("MetaVideoStatusResponseSchema parses transcoding status", () => {
    const raw = {
      id: "vid_987654321",
      status: {
        video_status: "ready",
        processing_phase: { status: "complete" },
      },
    };
    const parsed = MetaVideoStatusResponseSchema.parse(raw);
    assert.equal(parsed.status?.video_status, "ready");
  });

  it("MetaAdCreativeInputSchema validates creative contracts", () => {
    const valid = {
      name: "Enterizo Obsidiana Motion Promo",
      videoId: "vid_12345",
      pageId: "page_67890",
      body: "Descubre el nuevo enterizo con compresión anatómica inteligente.",
      link: "https://catalinaglamur.com/p/enterizo-obsidiana",
      callToActionType: "SHOP_NOW",
    };
    const parsed = MetaAdCreativeInputSchema.parse(valid);
    assert.equal(parsed.callToActionType, "SHOP_NOW");
    assert.equal(parsed.videoId, "vid_12345");
  });

  it("MetaAdInputSchema strictly defaults to PAUSED for HITL safety", () => {
    const input = {
      name: "Ad Campaign Test",
      adsetId: "adset_111",
      creativeId: "cr_222",
    };
    const parsed = MetaAdInputSchema.parse(input);
    assert.equal(parsed.status, "PAUSED");
  });

  it("MetaAdsClient formats clean WhatsApp HITL review notification", () => {
    const client = new MetaAdsClient({
      adAccountId: "123456789",
      accessToken: "mock_token",
    });

    const notification = client.formatAdReadyNotification({
      adName: "Campaña Lookbook Invierno",
      adId: "ad_999",
      creativeName: "Enterizo Escultor Obsidiana",
      previewUrl: "https://adsmanager.facebook.com/ads/preview/999",
    });

    assert.ok(notification.includes("Nuevo Anuncio en Borrador Listo para Revisión"));
    assert.ok(notification.includes("PAUSADO"));
    assert.ok(notification.includes("ad_999"));
  });
});
