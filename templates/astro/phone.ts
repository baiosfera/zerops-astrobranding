/**
 * Canonical E.164 Phone Normalization & Colombia (+57) Auto-Deduction Helper
 * Standardized for Zerops Web Runtimes & EvolutionGo Messaging Gateway
 */

export interface NormalizedPhone {
  canonical: string;
  whatsappDigits: string;
  display: string;
}

export function normalizePhone(raw: string): NormalizedPhone {
  const cleaned = raw.replace(/[^\d+]/g, '').trim();
  if (!cleaned) return { canonical: '', whatsappDigits: '', display: '' };

  let canonical = cleaned;
  if (!canonical.startsWith('+')) {
    const digitsOnly = canonical.replace(/\D/g, '');
    // Colombian mobile: 10 digits starting with 3 (e.g. 3101234567 -> +573101234567)
    if (digitsOnly.length === 10 && digitsOnly.startsWith('3')) {
      canonical = `+57${digitsOnly}`;
    } else if (digitsOnly.length === 12 && digitsOnly.startsWith('57')) {
      canonical = `+${digitsOnly}`;
    } else {
      canonical = `+${digitsOnly}`;
    }
  }

  const digits = canonical.replace(/\D/g, '');
  let display = canonical;
  if (canonical.startsWith('+57') && digits.length === 12) {
    display = `+57 ${digits.slice(2, 5)} ${digits.slice(5, 8)} ${digits.slice(8)}`;
  }

  return { canonical, whatsappDigits: digits, display };
}
