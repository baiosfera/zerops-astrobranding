/**
 * Canonical E.164 Phone Normalization Helper
 * Standardized for Zerops Web Runtimes & Messaging Gateways
 * Pure agnostic normalization without regional hardcoding.
 */

export interface NormalizedPhone {
  canonical: string;
  whatsappDigits: string;
  display: string;
}

export function normalizePhone(raw: string, defaultCountryPrefix: string = '+1'): NormalizedPhone {
  const cleaned = raw.replace(/[^\d+]/g, '').trim();
  if (!cleaned) return { canonical: '', whatsappDigits: '', display: '' };

  let canonical = cleaned;
  if (!canonical.startsWith('+')) {
    const digitsOnly = canonical.replace(/\D/g, '');
    canonical = `${defaultCountryPrefix}${digitsOnly}`;
  }

  const digits = canonical.replace(/\D/g, '');
  return { canonical, whatsappDigits: digits, display: canonical };
}
