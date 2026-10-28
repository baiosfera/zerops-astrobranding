import { createHmac } from "node:crypto";
import {
  MetaCatalogItemSchema,
  type MetaCatalogItem,
  type MetaCatalogChannelMetadata,
  type MetaCatalogBatchPayload,
  type MetaBatchMethod,
} from "@astrobranding/contracts";

/**
 * Escapes reserved XML characters to ensure standard compliance
 */
export function escapeXml(str: string): string {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/**
 * Generates an agnostic Meta Commerce / Google Merchant RSS 2.0 XML Catalog Feed
 */
export function generateMetaCatalogFeed(
  items: MetaCatalogItem[],
  channelMetadata: MetaCatalogChannelMetadata
): string {
  const channelTitle = escapeXml(channelMetadata.title);
  const channelLink = escapeXml(channelMetadata.link);
  const channelDesc = escapeXml(channelMetadata.description);

  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
  xml += `<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">\n`;
  xml += `  <channel>\n`;
  xml += `    <title>${channelTitle}</title>\n`;
  xml += `    <link>${channelLink}</link>\n`;
  xml += `    <description>${channelDesc}</description>\n`;

  for (const rawItem of items) {
    const item = MetaCatalogItemSchema.parse(rawItem);

    xml += `    <item>\n`;
    xml += `      <g:id>${escapeXml(item.id)}</g:id>\n`;
    xml += `      <g:title>${escapeXml(item.title)}</g:title>\n`;
    xml += `      <g:description>${escapeXml(item.description)}</g:description>\n`;
    xml += `      <g:link>${escapeXml(item.link)}</g:link>\n`;
    xml += `      <g:image_link>${escapeXml(item.image_link)}</g:image_link>\n`;
    xml += `      <g:brand>${escapeXml(item.brand)}</g:brand>\n`;
    xml += `      <g:condition>${escapeXml(item.condition)}</g:condition>\n`;
    xml += `      <g:availability>${escapeXml(item.availability)}</g:availability>\n`;
    xml += `      <g:price>${escapeXml(item.price)}</g:price>\n`;

    if (item.sale_price) {
      xml += `      <g:sale_price>${escapeXml(item.sale_price)}</g:sale_price>\n`;
    }
    if (item.item_group_id) {
      xml += `      <g:item_group_id>${escapeXml(item.item_group_id)}</g:item_group_id>\n`;
    }
    if (item.color) {
      xml += `      <g:color>${escapeXml(item.color)}</g:color>\n`;
    }
    if (item.size) {
      xml += `      <g:size>${escapeXml(item.size)}</g:size>\n`;
    }
    if (item.gender) {
      xml += `      <g:gender>${escapeXml(item.gender)}</g:gender>\n`;
    }
    if (item.age_group) {
      xml += `      <g:age_group>${escapeXml(item.age_group)}</g:age_group>\n`;
    }
    if (item.material) {
      xml += `      <g:material>${escapeXml(item.material)}</g:material>\n`;
    }
    if (item.pattern) {
      xml += `      <g:pattern>${escapeXml(item.pattern)}</g:pattern>\n`;
    }
    if (item.custom_label_0) {
      xml += `      <g:custom_label_0>${escapeXml(item.custom_label_0)}</g:custom_label_0>\n`;
    }
    if (item.custom_label_1) {
      xml += `      <g:custom_label_1>${escapeXml(item.custom_label_1)}</g:custom_label_1>\n`;
    }
    if (item.custom_label_2) {
      xml += `      <g:custom_label_2>${escapeXml(item.custom_label_2)}</g:custom_label_2>\n`;
    }
    if (item.custom_label_3) {
      xml += `      <g:custom_label_3>${escapeXml(item.custom_label_3)}</g:custom_label_3>\n`;
    }
    if (item.custom_label_4) {
      xml += `      <g:custom_label_4>${escapeXml(item.custom_label_4)}</g:custom_label_4>\n`;
    }

    if (item.additional_image_link && item.additional_image_link.length > 0) {
      for (const extraImg of item.additional_image_link) {
        xml += `      <g:additional_image_link>${escapeXml(extraImg)}</g:additional_image_link>\n`;
      }
    }

    xml += `    </item>\n`;
  }

  xml += `  </channel>\n`;
  xml += `</rss>\n`;

  return xml;
}

/**
 * Builds payload for Meta Items Batch API (Realtime SOTA Push)
 */
export function buildMetaBatchPayload(
  items: MetaCatalogItem[],
  options?: {
    method?: MetaBatchMethod;
    itemType?: "PRODUCT_ITEM" | "SERVICE_ITEM" | "HOME_LISTING" | "HOTEL" | "VEHICLE";
  }
): MetaCatalogBatchPayload {
  const method = options?.method || "CREATE";
  const itemType = options?.itemType || "PRODUCT_ITEM";

  const requests = items.map((raw) => {
    const item = MetaCatalogItemSchema.parse(raw);
    const data: Record<string, unknown> = {
      id: item.id,
      title: item.title,
      description: item.description,
      availability: item.availability,
      condition: item.condition,
      price: item.price,
      link: item.link,
      image_link: item.image_link,
      brand: item.brand,
    };

    if (item.sale_price) data.sale_price = item.sale_price;
    if (item.item_group_id) data.item_group_id = item.item_group_id;
    if (item.color) data.color = item.color;
    if (item.size) data.size = item.size;
    if (item.gender) data.gender = item.gender;
    if (item.age_group) data.age_group = item.age_group;
    if (item.material) data.material = item.material;
    if (item.pattern) data.pattern = item.pattern;
    if (item.custom_label_0) data.custom_label_0 = item.custom_label_0;
    if (item.custom_label_1) data.custom_label_1 = item.custom_label_1;
    if (item.custom_label_2) data.custom_label_2 = item.custom_label_2;
    if (item.custom_label_3) data.custom_label_3 = item.custom_label_3;
    if (item.custom_label_4) data.custom_label_4 = item.custom_label_4;
    if (item.inventory !== undefined) data.inventory = item.inventory;

    return {
      method,
      data,
    };
  });

  return {
    item_type: itemType,
    requests,
  };
}

export interface MetaCatalogPushConfig {
  accessToken?: string;
  appSecret?: string;
  graphApiVersion?: string;
  timeoutMs?: number;
}

export interface MetaCatalogBatchPushResult {
  success: boolean;
  handles?: string[];
  error?: string;
  statusCode?: number;
}

/**
 * Pushes a batch of catalog items to Meta Marketing API v21+
 */
export async function pushMetaCatalogBatch(
  catalogId: string,
  payload: MetaCatalogBatchPayload,
  config?: MetaCatalogPushConfig
): Promise<MetaCatalogBatchPushResult> {
  const accessToken =
    config?.accessToken ||
    process.env.META_CAPI_TOKEN ||
    process.env.META_CAPI_ACCESS_TOKEN;

  const appSecret =
    config?.appSecret ||
    process.env.META_APP_SECRET;

  const apiVersion = config?.graphApiVersion || "v21.0";
  const timeoutMs = config?.timeoutMs || 8000;

  if (!catalogId || !accessToken) {
    return {
      success: false,
      error: "Missing required Meta credentials: catalogId or accessToken is unset.",
    };
  }

  const cleanCatalogId = catalogId.trim();
  let endpoint = `https://graph.facebook.com/${apiVersion}/${cleanCatalogId}/items_batch`;

  if (appSecret) {
    const proof = createHmac("sha256", appSecret).update(accessToken).digest("hex");
    endpoint += `?appsecret_proof=${proof}`;
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
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timer);

    const result = (await response.json()) as {
      handles?: string[];
      error?: { message: string; type: string; code: number };
    };

    if (!response.ok || result.error) {
      return {
        success: false,
        statusCode: response.status,
        error: result.error?.message || `Meta API HTTP ${response.status}`,
      };
    }

    return {
      success: true,
      statusCode: response.status,
      handles: result.handles || [],
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      error: `Meta Catalog Batch dispatch error: ${message}`,
    };
  }
}
