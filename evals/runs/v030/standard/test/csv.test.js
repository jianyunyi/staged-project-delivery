const test = require('node:test');
const assert = require('node:assert/strict');
const {csv} = require('../csv');
const {exportCsv, list} = require('../service');
const {items} = require('../catalog');

// Independent CSV parser to check round trips across field and line boundaries.
const parseCsv = text => {
  const rows = []; let row = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { cell += '"'; i++; }
      else quoted = !quoted;
    } else if (!quoted && (char === ',' || char === '\n')) {
      row.push(cell); cell = '';
      if (char === '\n') { rows.push(row); row = []; }
    } else cell += char;
  }
  row.push(cell); rows.push(row);
  return rows;
};

test('AC-004 service exports all filtered rows regardless of pagination', () => {
  const options = {category:'drink', page:2, pageSize:1};
  assert.equal(list(options).items.length, 1);
  assert.equal(exportCsv(options), 'id,name,price\n1,茶,0\n2,咖啡,20');
  assert.equal(exportCsv(), 'id,name,price\n1,茶,0\n2,咖啡,20\n3,饼干,10');
  assert.equal(exportCsv({category:'missing'}), 'id,name,price\n');
  assert.equal(exportCsv({category:''}), 'id,name,price\n');
});
test('AC-005 exact escaping of commas, quotes, LF and CR', () => {
  const input = [{id:1,name:'茶,咖啡',price:0}, {id:2,name:'"茶"',price:20},
    {id:3,name:'a\nb',price:10}, {id:4,name:'a\rb',price:10}];
  const output = csv(input);
  assert.equal(output, 'id,name,price\n1,"茶,咖啡",0\n2,"""茶""",20\n3,"a\nb",10\n4,"a\rb",10');
  assert.deepEqual(parseCsv(output), [['id','name','price'], ...input.map(x => [String(x.id), x.name, String(x.price)])]);
});
test('AC-005 applies escaping to every column and preserves null/zero', () => {
  assert.equal(csv([{id:'x,y',name:null,price:'"5"'}]), 'id,name,price\n"x,y",,"""5"""');
  assert.equal(csv([{id:0,name:'普通中文',price:0}]), 'id,name,price\n0,普通中文,0');
});
test('AC-004/005 service integration exports special characters and CRLF', () => {
  const added = {id:4,name:'a,"b"\r\nc',category:'drink',price:0};
  items.push(added);
  try {
    const output = exportCsv({category:'drink',page:999,pageSize:1});
    assert.deepEqual(parseCsv(output), [['id','name','price'],['1','茶','0'],['2','咖啡','20'],['4',added.name,'0']]);
    assert.deepEqual(list({category:'drink',page:999,pageSize:1}), {items:[],total:3});
  } finally { items.pop(); }
});
