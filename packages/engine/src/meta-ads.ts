import * as fs from "node:fs";
import {
  MetaVideoUploadStartResponseSchema,
  MetaVideoStatusResponseSchema,
  MetaAdCreativeInputSchema,
  MetaAdInputSchema,
  MetaAdResultSchema,
  type MetaVideoUploadStartResponse,
  type MetaVideoStatusResponse,
  type MetaAdCreativeInput,
  type MetaAdInput,
  type MetaAdResult,
} from "@astrobranding/contracts";

export interface MetaAdsClientConfig {
  adAccountId?: string;
  accessToken?: string;
  apiVersion?: string;
  chunkSizeBytes?: number;
  maxPollSeconds?: number;
}

export class MetaAdsClient {
  private adAccountId: string;
  private accessToken: string;
  private apiVersion: string;
  private chunkSizeBytes: number;

  constructor(config?: MetaAdsClientConfig) {
    this.adAccountId =
      config?.adAccountId ||
      process.env.META_AD_ACCOUNT_ID ||
      process.env.META_ACT_ID ||
      "";
    this.accessToken =
      config?.accessToken ||
      process.env.META_ADS_TOKEN ||
      process.env.META_CAPI_TOKEN ||
      "";
    this.apiVersion = config?.apiVersion || "v21.0";
    // Default chunk size: 20 MB (safe for Meta Resumable Upload)
    this.chunkSizeBytes = config?.chunkSizeBytes || 20 * 1024 * 1024;
  }

  private getCleanAccountId(): string {
    const raw = this.adAccountId.trim();
    return raw.startsWith("act_") ? raw : `act_${raw}`;
  }

  /**
   * Resumable Chunked Video Upload complying with Meta Marketing API v21+
   * Reads bytes directly from local filesystem (localstorage) in 20MB chunks.
   */
  async uploadVideoResumable(
    filePath: string,
    options?: { title?: string; description?: string }
  ): Promise<{ videoId: string; uploadSessionId: string }> {
    if (!fs.existsSync(filePath)) {
      throw new Error(`Video file does not exist at path: ${filePath}`);
    }

    const fileSize = fs.statSync(filePath).size;
    const actId = this.getCleanAccountId();
    const endpoint = `https://graph.facebook.com/${this.apiVersion}/${actId}/advideos`;

    // Phase 1: Start
    const startUrl = new URL(endpoint);
    startUrl.searchParams.set("access_token", this.accessToken);
    startUrl.searchParams.set("upload_phase", "start");
    startUrl.searchParams.set("file_size", fileSize.toString());

    const startRes = await fetch(startUrl.toString(), { method: "POST" });
    const startData = await startRes.json();

    if (!startRes.ok || (startData as any).error) {
      throw new Error(
        `Meta Video Upload Start Failed: ${(startData as any).error?.message || startRes.statusText}`
      );
    }

    const { video_id: videoId, upload_session_id: uploadSessionId } =
      MetaVideoUploadStartResponseSchema.parse(startData);

    // Phase 2: Transfer Chunks
    const fileHandle = fs.openSync(filePath, "r");
    let currentStartOffset = 0;

    try {
      while (currentStartOffset < fileSize) {
        const bytesToRead = Math.min(this.chunkSizeBytes, fileSize - currentStartOffset);
        const buffer = Buffer.alloc(bytesToRead);
        fs.readSync(fileHandle, buffer, 0, bytesToRead, currentStartOffset);

        const formData = new FormData();
        formData.append("access_token", this.accessToken);
        formData.append("upload_phase", "transfer");
        formData.append("upload_session_id", uploadSessionId);
        formData.append("start_offset", currentStartOffset.toString());
        formData.append(
          "video_file_chunk",
          new Blob([buffer], { type: "video/mp4" }),
          "chunk.mp4"
        );

        const transferRes = await fetch(endpoint, {
          method: "POST",
          body: formData,
        });

        const transferData = (await transferRes.json()) as any;
        if (!transferRes.ok || transferData.error) {
          throw new Error(
            `Meta Video Upload Transfer Failed at offset ${currentStartOffset}: ${transferData.error?.message || transferRes.statusText}`
          );
        }

        const nextOffset = parseInt(transferData.start_offset, 10);
        if (nextOffset <= currentStartOffset && nextOffset < fileSize) {
          currentStartOffset += bytesToRead;
        } else {
          currentStartOffset = nextOffset;
        }
      }
    } finally {
      fs.closeSync(fileHandle);
    }

    // Phase 3: Finish
    const finishUrl = new URL(endpoint);
    finishUrl.searchParams.set("access_token", this.accessToken);
    finishUrl.searchParams.set("upload_phase", "finish");
    finishUrl.searchParams.set("upload_session_id", uploadSessionId);
    if (options?.title) finishUrl.searchParams.set("title", options.title);
    if (options?.description) finishUrl.searchParams.set("description", options.description);

    const finishRes = await fetch(finishUrl.toString(), { method: "POST" });
    const finishData = (await finishRes.json()) as any;

    if (!finishRes.ok || finishData.error) {
      throw new Error(
        `Meta Video Upload Finish Failed: ${finishData.error?.message || finishRes.statusText}`
      );
    }

    return { videoId, uploadSessionId };
  }

  /**
   * Polls Meta Video Transcoding status with exponential backoff until 'ready'
   */
  async pollVideoStatus(
    videoId: string,
    options?: { maxTimeoutSeconds?: number; initialDelayMs?: number }
  ): Promise<MetaVideoStatusResponse> {
    const maxTimeout = (options?.maxTimeoutSeconds || 180) * 1000;
    const startTime = Date.now();
    let delay = options?.initialDelayMs || 2000;

    while (Date.now() - startTime < maxTimeout) {
      const url = `https://graph.facebook.com/${this.apiVersion}/${videoId}?fields=status&access_token=${this.accessToken}`;
      const res = await fetch(url);
      const data = await res.json();

      if (res.ok && !(data as any).error) {
        const parsed = MetaVideoStatusResponseSchema.parse(data);
        const status = parsed.status?.video_status;
        if (status === "ready") {
          return parsed;
        }
        if (status === "error") {
          throw new Error(`Meta video transcoding failed for videoId: ${videoId}`);
        }
      }

      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * 1.5, 15000); // Exponential backoff capped at 15s
    }

    throw new Error(`Timeout waiting for video ${videoId} transcoding after ${maxTimeout / 1000}s`);
  }

  /**
   * Creates an AdCreative object referencing the transcode-ready video
   */
  async createAdCreative(input: MetaAdCreativeInput): Promise<MetaAdResult> {
    const parsed = MetaAdCreativeInputSchema.parse(input);
    const actId = this.getCleanAccountId();
    const endpoint = `https://graph.facebook.com/${this.apiVersion}/${actId}/adcreatives`;

    const objectStorySpec: Record<string, unknown> = {
      page_id: parsed.pageId,
      video_data: {
        video_id: parsed.videoId,
        title: parsed.title || parsed.name,
        message: parsed.body,
        call_to_action: {
          type: parsed.callToActionType,
          value: {
            link: parsed.link,
          },
        },
      },
    };

    if (parsed.instagramActorId) {
      objectStorySpec.instagram_actor_id = parsed.instagramActorId;
    }

    const payload = {
      name: parsed.name,
      object_story_spec: objectStorySpec,
    };

    const res = await fetch(`${endpoint}?access_token=${this.accessToken}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok || (data as any).error) {
      throw new Error(
        `Failed to create AdCreative: ${(data as any).error?.message || res.statusText}`
      );
    }

    return MetaAdResultSchema.parse(data);
  }

  /**
   * Creates an Ad in draft mode ('PAUSED') for Human-in-the-Loop review
   */
  async createAdDraft(input: MetaAdInput): Promise<MetaAdResult> {
    const parsed = MetaAdInputSchema.parse(input);
    const actId = this.getCleanAccountId();
    const endpoint = `https://graph.facebook.com/${this.apiVersion}/${actId}/ads`;

    const payload = {
      name: parsed.name,
      adset_id: parsed.adsetId,
      creative: { creative_id: parsed.creativeId },
      status: parsed.status, // Enforces 'PAUSED' by default
    };

    const res = await fetch(`${endpoint}?access_token=${this.accessToken}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok || (data as any).error) {
      throw new Error(
        `Failed to create Ad draft: ${(data as any).error?.message || res.statusText}`
      );
    }

    return MetaAdResultSchema.parse(data);
  }

  /**
   * WhatsApp Notification Bridge: formats notification when ad draft is ready for HITL review
   */
  formatAdReadyNotification(adDetails: {
    adName: string;
    adId: string;
    creativeName: string;
    previewUrl?: string;
  }): string {
    return [
      `🚀 *Nuevo Anuncio en Borrador Listo para Revisión*`,
      ``,
      `📌 *Campaña:* ${adDetails.adName}`,
      `🆔 *Ad ID:* \`${adDetails.adId}\``,
      `🎨 *Creativo:* ${adDetails.creativeName}`,
      `🛡️ *Estado:* PAUSADO (Esperando tu aprobación en Ads Manager)`,
      adDetails.previewUrl ? `🔗 *Preview:* ${adDetails.previewUrl}` : "",
      ``,
      `_Generado automáticamente por el Ecosistema Agéntico Meta Ads en Zerops._`
    ].filter(Boolean).join("\n");
  }
}
