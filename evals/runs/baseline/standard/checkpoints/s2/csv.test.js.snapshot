const test = require("node:test");
const assert = require("node:assert/strict");
const { csv } = require("./csv");
const { exportCsv, list } = require("./service");
const { items } = require("./catalog");

// Independent CSV reader: commas and line breaks delimit only outside quotes.
function parseCsv(text) {
  const rows = [];
  let row = [], value = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') { value += '"'; i++; }
      else if (char === '"') quoted = false;
      else value += char;
    } else if (char === '"') quoted = true;
    else if (char === ',') { row.push(value); value = ""; }
    else if (char === '\n' || char === '\r') {
      row.push(value); rows.push(row); row = []; value = "";
      if (char === '\r' && text[i + 1] === '\n') i++;
    } else value += char;
  }
  assert.equal(quoted, false, "CSV has a closing quote");
  if (value || row.length) { row.push(value); rows.push(row); }
  return rows;
}

test("AC-004 export filters exactly like list but ignores pagination", () => {
  const options = { category: "drink", page: 2, pageSize: 1 };
  assert.equal(list(options).items.length, 1);
  assert.equal(exportCsv(options), "id,name,price\n1,茶,0\n2,咖啡,20");
  assert.deepEqual(parseCsv(exportCsv(options)).slice(1).map(row => Number(row[0])), list({ category: "drink" }).items.map(x => x.id));
  assert.equal(exportCsv({ category: "unknown" }), "id,name,price\n");
  assert.equal(exportCsv({ category: "food", page: 999, pageSize: 1 }), "id,name,price\n3,饼干,10");
  assert.equal(parseCsv(exportCsv()).length, 4);
  for (const key of ["page", "pageSize"]) {
    for (const value of [0, -1, 1.5, "bad", null, true]) assert.throws(() => exportCsv({ [key]: value }), RangeError);
  }
});

test("AC-005 CSV escapes commas, quotes, CR/LF and preserves all three fields", () => {
  const names = ["普通", "含,逗号", '含"引号', "换\n行", "回\r车", '组合,\r\n"字符', ""];
  const records = names.map((name, id) => ({ id, name, price: id === 0 ? 0 : 1.25, category: "special" }));
  const encoded = csv(records);
  assert.ok(encoded.includes('"含,逗号"'));
  assert.ok(encoded.includes('"含""引号"'));
  assert.deepEqual(parseCsv(encoded), [["id", "name", "price"], ...records.map(x => [String(x.id), x.name, String(x.price)])]);
  assert.equal(csv([]), "id,name,price\n");
});

test("AC-004/005 service integration exports special fields and source stays unchanged", () => {
  const before = structuredClone(items);
  const records = [
    { id: 10, name: '茶, "香"\n新', category: "special", price: 0 },
    { id: 11, name: "咖\r\n啡", category: "special", price: 2 },
  ];
  try {
    items.push(...records);
    const options = { category: "special", page: 2, pageSize: 1 };
    assert.deepEqual(list(options), { items: [records[1]], total: 2 });
    assert.deepEqual(parseCsv(exportCsv(options)), [["id", "name", "price"], ["10", records[0].name, "0"], ["11", records[1].name, "2"]]);
    assert.deepEqual(items, [...before, ...records]);
  } finally {
    items.splice(0, items.length, ...before);
  }
});
