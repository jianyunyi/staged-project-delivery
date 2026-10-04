const test = require('node:test');
const assert = require('node:assert/strict');
const {csv} = require('./csv');
const {items} = require('./catalog');
const {list, exportCsv} = require('./service');

// An independent character-state parser: do not copy the writer's escaping logic.
function parseCsv(source) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < source.length; i++) {
    const char = source[i];
    if (char === '"') {
      if (quoted && source[i + 1] === '"') { field += '"'; i++; }
      else quoted = !quoted;
    } else if (!quoted && char === ',') { row.push(field); field = ''; }
    else if (!quoted && char === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else field += char;
  }
  assert.equal(quoted, false, 'CSV ends outside quoted field');
  if (field.length || row.length) { row.push(field); rows.push(row); }
  return rows;
}

test('AC-004 export filters exactly like list but ignores pagination', () => {
  assert.equal(list({category: 'drink', page: 2, pageSize: 1}).items.length, 1);
  assert.equal(exportCsv({category: 'drink', page: 2, pageSize: 1}), 'id,name,price\n1,茶,0\n2,咖啡,20');
  assert.equal(exportCsv({category: 'food'}), 'id,name,price\n3,饼干,10');
  assert.equal(exportCsv({category: 'DRINK'}), 'id,name,price\n');
});

test('AC-004 default export is full and pagination has no validation effect', () => {
  assert.equal(parseCsv(exportCsv()).length, items.length + 1);
  assert.equal(exportCsv({page: 0, pageSize: 'bad'}), exportCsv());
  assert.equal(exportCsv({category: 'unknown'}), 'id,name,price\n');
});

test('AC-005 exact header, zero price and only selected fields', () => {
  assert.equal(csv([{id: 1, name: '茶', price: 0, category: 'drink', secret: 'hidden'}]), 'id,name,price\n1,茶,0');
  assert.equal(csv([]), 'id,name,price\n');
});

test('AC-005 special characters in every field round trip independently', () => {
  const records = [
    {id: 'id,one', name: '茶,咖啡', price: '0,00'},
    {id: 'id"two', name: '他说"好"', price: '"1"'},
    {id: 'id\nthree', name: '第一行\n第二行', price: '1\r2'},
    {id: 4, name: '混合,"引用"\r\n下一行', price: 0},
  ];
  assert.deepEqual(parseCsv(csv(records)), [
    ['id', 'name', 'price'],
    ...records.map(record => [String(record.id), record.name, String(record.price)]),
  ]);
  assert.equal(csv([{id: 1, name: 'a,"b"\nnext', price: 0}]), 'id,name,price\n1,"a,""b""\nnext",0');
});

test('AC-004/005 service exports more than the default page with CSV escaping', () => {
  const count = items.length;
  const fixture = Array.from({length: 12}, (_, n) => ({id: n + 100, category: 'fixture', name: `商品, "${n}"\n行`, price: n}));
  try {
    items.push(...fixture);
    assert.equal(list({category: 'fixture'}).items.length, 10);
    assert.equal(list({category: 'fixture'}).total, 12);
    assert.deepEqual(parseCsv(exportCsv({category: 'fixture', page: 2, pageSize: 1})), [
      ['id', 'name', 'price'],
      ...fixture.map(item => [String(item.id), item.name, String(item.price)]),
    ]);
  } finally { items.splice(count); }
});
