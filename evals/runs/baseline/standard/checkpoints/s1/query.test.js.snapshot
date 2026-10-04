const test = require("node:test");
const assert = require("node:assert/strict");
const { query } = require("./query");
const { list } = require("./service");
const { items } = require("./catalog");

test("AC-001 category filtering is exact and leaves source intact", () => {
  const before = structuredClone(items);
  assert.deepEqual(query(items, { category: "drink" }).items.map(x => x.id), [1, 2]);
  assert.deepEqual(query(items, { category: "food" }).items.map(x => x.id), [3]);
  assert.deepEqual(query(items, { category: "unknown" }), { items: [], total: 0 });
  assert.deepEqual(query(items, { category: "" }), { items: [], total: 0 });
  assert.deepEqual(items, before);
});

test("AC-002 valid pagination, numeric strings, defaults and out-of-range pages", () => {
  assert.deepEqual(query(items), { items, total: 3 });
  assert.deepEqual(query(items, { page: 2, pageSize: 1 }), { items: [items[1]], total: 3 });
  assert.deepEqual(query(items, { page: "02", pageSize: "1" }), { items: [items[1]], total: 3 });
  assert.deepEqual(query(items, { page: 4, pageSize: 1 }), { items: [], total: 3 });
  assert.deepEqual(query(items, { page: Number.MAX_SAFE_INTEGER, pageSize: Number.MAX_SAFE_INTEGER }), { items: [], total: 3 });
  const many = Array.from({ length: 12 }, (_, id) => ({ id }));
  assert.equal(query(many).items.length, 10);
  assert.deepEqual(query(many, { page: 2 }).items, many.slice(10));
});

test("AC-002 invalid page and pageSize raise clear errors", () => {
  const invalid = [0, -1, 1.2, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1, "", " ", "1.0", "1e2", "-1", "0", "2x", null, true, {}, []];
  for (const key of ["page", "pageSize"]) {
    for (const value of invalid) {
      assert.throws(() => list({ [key]: value }), error => error instanceof RangeError && error.message.includes(key));
    }
  }
  for (const options of [null, 1, "x", []]) assert.throws(() => list(options), TypeError);
});

test("AC-003 list returns items and the total before pagination", () => {
  assert.deepEqual(list({ category: "drink", page: 2, pageSize: 1 }), { items: [items[1]], total: 2 });
  assert.deepEqual(list(), { items, total: 3 });
  assert.deepEqual(list({ category: "drink", page: 3, pageSize: 1 }), { items: [], total: 2 });
  assert.equal(list().items[0].price, 0);
});
