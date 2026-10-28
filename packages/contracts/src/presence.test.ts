import { describe, it, expect } from "bun:test";
import { BrandPresenceProfileSchema } from "./presence";
import { OfferingSchema } from "./offerings";
import { CommercialSignalSchema, ConsentModeV2Schema } from "./telemetry";

describe("@astrobranding/contracts", () => {
  it("should validate a Service Area Business (SAB) profile without street address", () => {
    const sab = BrandPresenceProfileSchema.parse({
      presence_model: "service_area_business",
      business_name: "Catalina Glamur",
      website_url: "https://catalinaglamur.com",
      schema_org_type: "ProfessionalService",
      service_areas: ["Envigado", "Sabaneta", "Medellín Sur"],
      same_as_urls: ["https://instagram.com/catalinaglamur"],
    });

    expect(sab.presence_model).toBe("service_area_business");
    expect(sab.service_areas).toHaveLength(3);
    expect(sab.street_address).toBeUndefined();
  });

  it("should validate an offering across archetypes", () => {
    const offering = OfferingSchema.parse({
      id: crypto.randomUUID(),
      sku: "CAT-LIP-01",
      title: "Labial Blindado Catalina Glamur",
      description: "Pigmento larga duración para labios impecables",
      archetype: "physical_goods",
      channel_strategy: "commerce_feed",
      price: 65000,
      currency: "COP",
      url: "https://catalinaglamur.com/shop/labial-blindado",
      image_url: "https://catalinaglamur.com/assets/labial.jpg",
      brand: "Catalina Glamur",
    });

    expect(offering.archetype).toBe("physical_goods");
    expect(offering.channel_strategy).toBe("commerce_feed");
  });

  it("should validate Google Consent Mode v2 defaults", () => {
    const consent = ConsentModeV2Schema.parse({});
    expect(consent.ad_storage).toBe("denied");
    expect(consent.ad_user_data).toBe("denied");
    expect(consent.ad_personalization).toBe("denied");
    expect(consent.analytics_storage).toBe("denied");
  });

  it("should validate Commercial Signal with attribution session", () => {
    const signal = CommercialSignalSchema.parse({
      event_id: "evt_12345",
      event_name: "Purchase",
      event_source_url: "https://catalinaglamur.com/checkout/success",
      content_type: "product",
      value: 130000,
      currency: "COP",
      user_data: {
        email: "test@example.com",
        phone: "+573001234567",
        fbc: "fb.1.1730000000.IwAR123",
      },
    });

    expect(signal.event_name).toBe("Purchase");
    expect(signal.value).toBe(130000);
  });
});
