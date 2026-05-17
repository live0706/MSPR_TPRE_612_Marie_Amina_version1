import test from "node:test";
import assert from "node:assert/strict";

import {
  buildOperatorHighlights,
  buildVolumeHighlights,
  formatCompact,
  formatMetric,
  formatTimestamp,
  serviceSplit
} from "../src/utils.js";

test("formatCompact formats integer values with French locale", () => {
  assert.equal(formatCompact(145023), "145\u202f023");
});

test("formatMetric preserves decimals and suffix", () => {
  assert.equal(formatMetric(1.2345, 3, " kg"), "1,235 kg");
});

test("formatTimestamp returns fallback when input is invalid", () => {
  assert.equal(formatTimestamp("not-a-date"), "Non disponible");
});

test("buildOperatorHighlights groups journeys by operator and country", () => {
  const result = buildOperatorHighlights([
    { operator_name: "NightJet", country_code: "AT" },
    { operator_name: "NightJet", country_code: "DE" },
    { operator_name: "SNCF", country_code: "FR" }
  ]);

  assert.equal(result[0].operator, "NightJet");
  assert.equal(result[0].count, 2);
  assert.equal(result[0].countries, "AT, DE");
});

test("buildVolumeHighlights returns the most active countries first", () => {
  const result = buildVolumeHighlights([
    { country_code: "FR", total_trajets: 12 },
    { country_code: "DE", total_trajets: 18 },
    { country_code: "AT", total_trajets: 7 }
  ]);

  assert.deepEqual(
    result.map((item) => item.country_code),
    ["DE", "FR", "AT"]
  );
});

test("serviceSplit computes day and night shares", () => {
  const result = serviceSplit([
    { train_type: "night", train_count: 30 },
    { train_type: "day", train_count: 70 }
  ]);

  assert.deepEqual(result, { nightShare: 30, dayShare: 70 });
});
