/**
 * Pluggable Discount & Affiliate Strategy Engine (Lego Pattern)
 * Universal template for Zerops Astro-Web runtimes
 * 
 * Supports:
 * - Standard Rate (Default): For brands without discounts or affiliates.
 * - Single-Use Per Domain: Discretionary 10% discount for 1st purchase per domain.
 * - All Purchases: Continuous affiliate discount.
 * 
 * Selection via process.env.DISCOUNT_STRATEGY: "standard_rate" | "single_use_per_domain" | "all_purchases"
 */

export type DiscountDomain = "event_ticket" | "membership" | "product" | "service" | string;

export interface DiscountContext {
  domain: DiscountDomain;
  whatsapp?: string | null;
  email?: string | null;
  affiliateRef?: string | null;
  isVipActive?: boolean;
}

export interface DiscountResult {
  hasDiscount: boolean;
  discountRate: number; // e.g. 0.10 or 0
  reason: string;
  strategy: string;
}

export interface DiscountStrategy {
  name: string;
  calculate(ctx: DiscountContext): Promise<DiscountResult>;
}

/**
 * Standard Rate Strategy (Default for brands without affiliate discounts)
 */
export class StandardRateStrategy implements DiscountStrategy {
  name = "standard_rate";

  async calculate(_ctx: DiscountContext): Promise<DiscountResult> {
    return {
      hasDiscount: false,
      discountRate: 0,
      reason: "standard_rate",
      strategy: this.name,
    };
  }
}

/**
 * Continuous Strategy (Affiliate discount applied to every purchase with referral)
 */
export class AllPurchasesDiscountStrategy implements DiscountStrategy {
  name = "all_purchases";

  async calculate(ctx: DiscountContext): Promise<DiscountResult> {
    if (ctx.affiliateRef || ctx.isVipActive) {
      return {
        hasDiscount: true,
        discountRate: 0.10,
        reason: "continuous_affiliate_discount",
        strategy: this.name,
      };
    }
    return {
      hasDiscount: false,
      discountRate: 0,
      reason: "standard_rate",
      strategy: this.name,
    };
  }
}

/**
 * Single-Use Per Domain Strategy (Pluggable strategy for single-use discounts per independent category)
 */
export class SingleUsePerDomainStrategy implements DiscountStrategy {
  name = "single_use_per_domain";

  async calculate(ctx: DiscountContext): Promise<DiscountResult> {
    const { domain, affiliateRef, isVipActive } = ctx;

    // Active VIP / Preferred members maintain permanent privilege
    if (isVipActive) {
      return {
        hasDiscount: true,
        discountRate: 0.10,
        reason: "preferred_member_privilege",
        strategy: this.name,
      };
    }

    // Without affiliate referral, regular standard rate applies
    if (!affiliateRef || affiliateRef.trim() === "") {
      return {
        hasDiscount: false,
        discountRate: 0,
        reason: "standard_rate",
        strategy: this.name,
      };
    }

    // Default grant 10% on first order (to be wired against database purchase history in downstream app)
    return {
      hasDiscount: true,
      discountRate: 0.10,
      reason: `first_purchase_in_${domain}`,
      strategy: this.name,
    };
  }
}

// Registry of available strategies
const strategies: Record<string, DiscountStrategy> = {
  standard_rate: new StandardRateStrategy(),
  all_purchases: new AllPurchasesDiscountStrategy(),
  single_use_per_domain: new SingleUsePerDomainStrategy(),
};

/**
 * Primary resolver for checkout discounts across all business domains
 */
export async function resolveDiscount(ctx: DiscountContext): Promise<DiscountResult> {
  const strategyKey = process.env.DISCOUNT_STRATEGY || "standard_rate";
  const strategy = strategies[strategyKey] || strategies.standard_rate;
  return strategy.calculate(ctx);
}
