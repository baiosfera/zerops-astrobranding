import test from "node:test";
import assert from "node:assert/strict";
import {
  hashMetaField,
  hashMetaEmail,
  hashMetaPhone,
  generateMetaSharedEventId,
  prepareMetaUserData,
} from "./meta-capi.ts";

test("hashMetaEmail normalizes and hashes properly", () => {
  const email = "  Test.User@Example.COM ";
  const hashed = hashMetaEmail(email);
  assert.ok(hashed);
  assert.equal(hashed.length, 64); // SHA-256 hex length
  // sha256 of "test.user@example.com"
  const expected = "a97d7a4513204a9cc7cb2f11d72d41a59b18d1ba633d22e58d53c625518f5203";
  assert.equal(hashed, expected);
});

test("hashMetaPhone strips formatting and formats E.164", () => {
  const phone = "+57 (300) 123-4567";
  const hashed = hashMetaPhone(phone);
  assert.ok(hashed);
  assert.equal(hashed.length, 64);
  // digits: 573001234567
  const cleanPhone = "300 123 4567";
  const hashedAuto = hashMetaPhone(cleanPhone);
  assert.equal(hashed, hashedAuto);
});

test("generateMetaSharedEventId produces consistent prefix format", () => {
  const eventId = generateMetaSharedEventId("glamur");
  assert.ok(eventId.startsWith("glamur-"));
  const parts = eventId.split("-");
  assert.ok(parts.length >= 3);
});

test("prepareMetaUserData keeps network cookies unhashed and hashes PII", () => {
  const userData = {
    email: "cliente@catalinaglamur.com",
    phone: "3109876543",
    fbp: "fb.1.1712345678.987654321",
    fbc: "fb.1.1712345678.AbCdEf",
    clientIp: "190.24.50.12",
    userAgent: "Mozilla/5.0",
  };

  const prepared = prepareMetaUserData(userData);
  assert.equal(prepared.fbp, "fb.1.1712345678.987654321");
  assert.equal(prepared.fbc, "fb.1.1712345678.AbCdEf");
  assert.equal(prepared.client_ip_address, "190.24.50.12");
  assert.equal(prepared.client_user_agent, "Mozilla/5.0");
  assert.ok(Array.isArray(prepared.em));
  assert.equal(prepared.em[0].length, 64);
  assert.ok(Array.isArray(prepared.ph));
  assert.equal(prepared.ph[0].length, 64);
});
