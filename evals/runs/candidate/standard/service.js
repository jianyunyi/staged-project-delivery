const {items} = require('./catalog');
const {query, filterItems} = require('./query');
const {csv} = require('./csv');

exports.list = options => query(items, options);
exports.exportCsv = options => csv(filterItems(items, options));
