const {test}=require("node:test");const assert=require("node:assert/strict");const {formatPrice}=require("./price");
test("prices",()=>{assert.equal(formatPrice(0),"0.00");assert.equal(formatPrice(12.3),"12.30");assert.equal(formatPrice(null),"—");assert.equal(formatPrice(undefined),"—");assert.equal(formatPrice(NaN),"—");});
