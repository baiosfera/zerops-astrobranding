import test from "node:test";
import assert from "node:assert/strict";
import {
  escapeXml,
  generateMetaCatalogFeed,
  buildMetaBatchPayload,
  pushMetaCatalogBatch,
} from "./catalog-feed.ts";
import {
  MetaCatalogItemSchema,
  MetaCatalogBatchPayloadSchema,
} from "@astrobranding/contracts";

test("escapeXml correctly sanitizes XML entities", () => {
  const unsafe = `Lingerie & "Glamour" <Boutique> 'Exclusive'`;
  const safe = escapeXml(unsafe);
  assert.equal(
    safe,
    `Lingerie &amp; &quot;Glamour&quot; &lt;Boutique&gt; &apos;Exclusive&apos;`
  );
});

test("MetaCatalogItemSchema validates valid products and services", () => {
  const validProduct = {
    id: "SKU-001",
    title: "Enterizo Escultor Blanco",
    description: "Compresión gradual seamless 380g",
    availability: "in stock",
    condition: "new",
    price: "80000 COP",
    link: "https://catalinaglamur.com/p/enterizo-escultor-blanco",
    image_link: "https://catalinaglamur.com/images/products/product-01.jpg",
    brand: "Catalina Glamur",
    item_group_id: "GRP-ESCULTOR",
    color: "Blanco",
    size: "S",
    custom_label_0: "bestseller",
  };

  const parsed = MetaCatalogItemSchema.parse(validProduct);
  assert.equal(parsed.id, "SKU-001");
  assert.equal(parsed.price, "80000 COP");

  // Invalid price should throw
  assert.throws(() => {
    MetaCatalogItemSchema.parse({
      ...validProduct,
      price: "80000", // missing currency
    });
  });
});

test("generateMetaCatalogFeed outputs standard RSS 2.0 XML with Google namespace", () => {
  const channel = {
    title: "Catalina Glamur Meta Catalog",
    link: "https://catalinaglamur.com",
    description: "Alta Costura y Soberanía Textil",
    brand: "Catalina Glamur",
  };

  const items = [
    {
      id: "SKU-001",
      title: "Enterizo Escultor Blanco & Dorado",
      description: "Compresión inteligente sin transparencias",
      availability: "in stock",
      condition: "new",
      price: "80000.00 COP",
      sale_price: "72000.00 COP",
      link: "https://catalinaglamur.com/p/enterizo-escultor-blanco",
      image_link: "https://catalinaglamur.com/images/products/product-01.jpg",
      additional_image_link: [
        "https://catalinaglamur.com/images/products/product-01-back.jpg"
      ],
      brand: "Catalina Glamur",
      item_group_id: "GRP-ESCULTOR",
      color: "Blanco",
      size: "M",
      custom_label_0: "hero_lookbook",
    },
  ];

  const xml = generateMetaCatalogFeed(items, channel);

  assert.ok(xml.startsWith(`<?xml version="1.0" encoding="UTF-8"?>`));
  assert.ok(xml.includes(`<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">`));
  assert.ok(xml.includes(`<title>Catalina Glamur Meta Catalog</title>`));
  assert.ok(xml.includes(`<g:id>SKU-001</g:id>`));
  assert.ok(xml.includes(`<g:title>Enterizo Escultor Blanco &amp; Dorado</g:title>`));
  assert.ok(xml.includes(`<g:price>80000.00 COP</g:price>`));
  assert.ok(xml.includes(`<g:sale_price>72000.00 COP</g:sale_price>`));
  assert.ok(xml.includes(`<g:item_group_id>GRP-ESCULTOR</g:item_group_id>`));
  assert.ok(xml.includes(`<g:custom_label_0>hero_lookbook</g:custom_label_0>`));
  assert.ok(xml.includes(`<g:additional_image_link>https://catalinaglamur.com/images/products/product-01-back.jpg</g:additional_image_link>`));
  assert.ok(xml.endsWith(`</rss>\n`));
});

test("buildMetaBatchPayload generates valid realtime Items Batch API payload", () => {
  const items = [
    {
      id: "SRV-MAQ-01",
      title: "Atelier Maquillaje Social",
      description: "Técnica Piel Blindada de Larga Fijación",
      availability: "in stock",
      condition: "new",
      price: "200000 COP",
      link: "https://catalinaglamur.com/servicios/maquillaje-social",
      image_link: "https://catalinaglamur.com/images/services/maquillaje-social-1.jpg",
      brand: "Catalina Glamur",
      vertical: "services",
      service_type: "makeup",
      custom_label_1: "atelier",
    },
  ];

  const payload = buildMetaBatchPayload(items, {
    method: "CREATE",
    itemType: "SERVICE_ITEM",
  });

  assert.equal(payload.item_type, "SERVICE_ITEM");
  assert.equal(payload.requests.length, 1);
  assert.equal(payload.requests[0].method, "CREATE");
  assert.equal(payload.requests[0].data.id, "SRV-MAQ-01");
  assert.equal(payload.requests[0].data.price, "200000 COP");

  // Validates with Zod
  const validated = MetaCatalogBatchPayloadSchema.parse(payload);
  assert.equal(validated.requests[0].method, "CREATE");
});

test("pushMetaCatalogBatch gracefully handles missing credentials", async () => {
  const result = await pushMetaCatalogBatch("", {
    item_type: "PRODUCT_ITEM",
    requests: [],
  });

  assert.equal(result.success, false);
  assert.ok(result.error?.includes("Missing required Meta credentials"));
});
