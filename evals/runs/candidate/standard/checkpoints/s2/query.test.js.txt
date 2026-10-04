const test = require('node:test');
const assert = require('node:assert/strict');
const {query} = require('./query');
const {items} = require('./catalog');
const {list} = require('./service');

test('AC-001 category filtering is exact and does not mutate catalog', () => {
  const before = JSON.stringify(items);
  assert.deepEqual(query(items, {category: 'drink'}), {items: items.slice(0, 2), total: 2});
  assert.deepEqual(query(items, {category: 'unknown'}), {items: [], total: 0});
  assert.deepEqual(query(items, {category: 'DRINK'}), {items: [], total: 0});
  assert.equal(JSON.stringify(items), before);
});

test('AC-002 filtering precedes pagination and total is not page length', () => {
  assert.deepEqual(query(items, {category: 'drink', page: 2, pageSize: 1}), {items: [items[1]], total: 2});
  assert.deepEqual(query(items, {page: 2, pageSize: 2}), {items: [items[2]], total: 3});
});

test('AC-002 defaults and service integration return items and total', () => {
  assert.deepEqual(list(), {items, total: 3});
  assert.deepEqual(list({category: 'food', page: 1, pageSize: 1}), {items: [items[2]], total: 1});
  const defaults = Array.from({length: 12}, (_, id) => ({id}));
  assert.deepEqual(query(defaults), {items: defaults.slice(0, 10), total: 12});
});

test('AC-002 empty and far out of range pages preserve total', () => {
  assert.deepEqual(query([], {page: 2}), {items: [], total: 0});
  assert.deepEqual(query(items, {page: 4, pageSize: 1}), {items: [], total: 3});
  assert.deepEqual(query(items, {page: Number.MAX_SAFE_INTEGER, pageSize: Number.MAX_SAFE_INTEGER}), {items: [], total: 3});
});

test('AC-003 positive numeric strings and integers are accepted', () => {
  assert.deepEqual(list({page: '2', pageSize: '1'}), {items: [items[1]], total: 3});
  assert.deepEqual(query(items, {page: 1, pageSize: Number.MAX_SAFE_INTEGER}), {items, total: 3});
});

test('AC-003 illegal values throw for both pagination parameters', () => {
  const invalid = [0, -1, 1.5, '', ' ', 'abc', '1.2', '1e2', '0', '-1', true, false, null, NaN, Infinity, -Infinity, {}, [], Number.MAX_SAFE_INTEGER + 1, '9007199254740992'];
  for (const name of ['page', 'pageSize']) {
    for (const value of invalid) {
      assert.throws(() => list({[name]: value}), error => error instanceof RangeError && error.message.includes(name), `${name}: ${String(value)}`);
    }
  }
});

test('AC-003 invalid pagination fails even when category matches nothing', () => {
  assert.throws(() => query(items, {category: 'unknown', page: 0}), RangeError);
});
