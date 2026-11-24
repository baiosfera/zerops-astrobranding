/**
 * Canonical E.164 Phone Normalization Helper
 * Standardized for Zerops Web Runtimes & Messaging Gateways (CO +57 default, INTL-safe)
 */

export interface NormalizedPhone {
  canonical: string;
  whatsappDigits: string;
  display: string;
}

export function normalizePhone(raw: string, defaultCountryPrefix: string = '+57'): NormalizedPhone {
  let cleaned = raw.replace(/[^\d+]/g, '').trim();
  if (!cleaned) return { canonical: '', whatsappDigits: '', display: '' };

  if (cleaned.startsWith('00')) {
    cleaned = `+${cleaned.slice(2)}`;
  }

  let canonical = cleaned;
  if (!canonical.startsWith('+')) {
    const digitsOnly = canonical.replace(/\D/g, '');
    if (defaultCountryPrefix === '+57' && digitsOnly.startsWith('57') && digitsOnly.length === 12) {
      canonical = `+${digitsOnly}`;
    } else if (defaultCountryPrefix === '+57' && digitsOnly.length === 10 && digitsOnly.startsWith('3')) {
      canonical = `+57${digitsOnly}`;
    } else {
      canonical = `${defaultCountryPrefix}${digitsOnly}`;
    }
  }

  const digits = canonical.replace(/\D/g, '');
  return { canonical, whatsappDigits: digits, display: canonical };
}

/**
 * Generates deduplicated lookup variants (+57..., 57..., local 10-digit)
 * so WhatsApp JID / CRM queries match consistently across formats.
 */
export function getPhoneVariants(raw: string, defaultCountryPrefix: string = '+57'): string[] {
  const normalized = normalizePhone(raw, defaultCountryPrefix);
  if (!normalized.canonical) return [];

  const variants = new Set<string>([normalized.canonical, normalized.whatsappDigits]);
  if (normalized.whatsappDigits.startsWith('57') && normalized.whatsappDigits.length === 12) {
    variants.add(normalized.whatsappDigits.slice(2));
  }
  return Array.from(variants);
}
