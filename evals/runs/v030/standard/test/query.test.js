const test = require('node:test');
const assert = require('node:assert/strict');
const {query} = require('../query');
const {items} = require('../catalog');
const {list} = require('../service');

test('AC-001 default and exact category filtering', () => {
  assert.deepEqual(query(items), {items, total: 3});
  assert.deepEqual(query(items, {category:'drink'}), {items:items.slice(0, 2), total:2});
  assert.deepEqual(query(items, {category:'missing'}), {items:[], total:0});
  assert.deepEqual(query(items, {category:''}), {items:[], total:0});
  assert.deepEqual(query([{category:''}], {category:''}).items, [{category:''}]);
});
test('AC-002 pagination follows filtering and preserves total', () => {
  assert.deepEqual(list({category:'drink', page:2, pageSize:1}), {items:[items[1]], total:2});
  assert.deepEqual(query(items, {page:4, pageSize:1}), {items:[], total:3});
  assert.deepEqual(query(items, {page:Number.MAX_SAFE_INTEGER, pageSize:Number.MAX_SAFE_INTEGER}), {items:[], total:3});
  assert.deepEqual(query([], {page:1, pageSize:1}), {items:[], total:0});
});
test('AC-002 default options and no input mutation', () => {
  const source = Object.freeze(items.slice());
  assert.deepEqual(list(), {items, total:3});
  assert.deepEqual(query(source, {pageSize:1}), {items:[items[0]], total:3});
  assert.deepEqual(source, items);
});
for (const name of ['page', 'pageSize']) {
  test(`AC-003 rejects invalid ${name}`, () => {
    for (const value of [0, -1, 1.5, NaN, Infinity, '1', null, true, Number.MAX_SAFE_INTEGER + 1]) {
      assert.throws(() => list({[name]:value}), error => error instanceof RangeError && error.message.includes(name));
    }
  });
}
