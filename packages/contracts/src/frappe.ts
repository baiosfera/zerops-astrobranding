import { z } from "zod";

/**
 * Frappe CRM v1.83+ & ERPNext Contracts
 */
export const FrappeLeadSchema = z.object({
  name: z.string().optional(), // CRM-LEAD-XXXX
  first_name: z.string(),
  last_name: z.string().optional(),
  lead_name: z.string().optional(),
  email: z.string().email(),
  mobile_no: z.string().optional(),
  status: z.enum(["Lead", "Open", "Replied", "Opportunity", "Quotation", "LostConverted", "Qualified"]).optional().default("Lead"),
  organization: z.string().optional(),
});

export type FrappeLead = z.infer<typeof FrappeLeadSchema>;
export type FrappeLeadInput = z.input<typeof FrappeLeadSchema>;

export const FrappeDealSchema = z.object({
  name: z.string().optional(), // CRM-DEAL-XXXX
  lead: z.string(), // FK -> CRM Lead name
  deal_name: z.string().optional(),
  deal_value: z.number(),
  currency: z.string().optional().default("USD"),
  status: z.enum(["Open", "Demo/Making", "Proposal Sent", "Negotiation", "Won", "Lost"]).optional().default("Open"),
  organization: z.string().optional(),
  email: z.string().email().optional(),
  mobile_no: z.string().optional(),
});

export type FrappeDeal = z.infer<typeof FrappeDealSchema>;
export type FrappeDealInput = z.input<typeof FrappeDealSchema>;

export const FrappeCustomerSchema = z.object({
  name: z.string().optional(),
  customer_name: z.string(),
  customer_type: z.enum(["Individual", "Company"]).optional().default("Individual"),
  customer_group: z.string().optional().default("Individual"),
  territory: z.string().optional().default("All Territories"),
  email_id: z.string().email().optional(),
  mobile_no: z.string().optional(),
});

export type FrappeCustomer = z.infer<typeof FrappeCustomerSchema>;
export type FrappeCustomerInput = z.input<typeof FrappeCustomerSchema>;

export const FrappeSalesInvoiceItemSchema = z.object({
  item_code: z.string().optional().default("ASTRO-REPORT"),
  item_name: z.string(),
  qty: z.number().optional().default(1),
  rate: z.number(),
  amount: z.number(),
});

export const FrappeSalesInvoiceSchema = z.object({
  name: z.string().optional(), // ACC-SINV-XXXX
  customer: z.string(),
  posting_date: z.string().optional(),
  currency: z.string().optional().default("USD"),
  items: z.array(FrappeSalesInvoiceItemSchema),
  dian_cufe: z.string().optional(),
  is_pos: z.number().optional().default(0),
});

export type FrappeSalesInvoice = z.infer<typeof FrappeSalesInvoiceSchema>;
export type FrappeSalesInvoiceInput = z.input<typeof FrappeSalesInvoiceSchema>;

export const FrappeDocTypeTargetSchema = z.enum([
  "CRM Lead",
  "CRM Deal",
  "Sales Order",
  "Sales Invoice",
  "Subscription",
]);

export type FrappeDocTypeTarget = z.infer<typeof FrappeDocTypeTargetSchema>;

export const OfferingToFrappeMappingSchema = z.object({
  archetype: z.enum([
    "physical_goods",
    "courses_education",
    "memberships_mrr",
    "events_ticketing",
    "digital_products",
    "service_bookings",
  ]),
  target_doctype: FrappeDocTypeTargetSchema,
  is_stock_item: z.boolean(),
  requires_delivery_note: z.boolean(),
  crm_qualification_required: z.boolean(),
});

export type OfferingToFrappeMapping = z.infer<typeof OfferingToFrappeMappingSchema>;

export function getFrappeMappingForArchetype(
  archetype: "physical_goods" | "courses_education" | "memberships_mrr" | "events_ticketing" | "digital_products" | "service_bookings"
): OfferingToFrappeMapping {
  switch (archetype) {
    case "physical_goods":
      return {
        archetype,
        target_doctype: "Sales Order",
        is_stock_item: true,
        requires_delivery_note: true,
        crm_qualification_required: false,
      };
    case "courses_education":
    case "digital_products":
      return {
        archetype,
        target_doctype: "Sales Invoice",
        is_stock_item: false,
        requires_delivery_note: false,
        crm_qualification_required: false,
      };
    case "memberships_mrr":
      return {
        archetype,
        target_doctype: "Subscription",
        is_stock_item: false,
        requires_delivery_note: false,
        crm_qualification_required: false,
      };
    case "events_ticketing":
      return {
        archetype,
        target_doctype: "Sales Invoice",
        is_stock_item: false,
        requires_delivery_note: false,
        crm_qualification_required: false,
      };
    case "service_bookings":
      return {
        archetype,
        target_doctype: "CRM Lead",
        is_stock_item: false,
        requires_delivery_note: false,
        crm_qualification_required: true,
      };
  }
}

