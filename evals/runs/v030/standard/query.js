exports.filterItems = (items, options = {}) => options.category === undefined
  ? items.slice()
  : items.filter(item => item.category === options.category);

exports.query = (items, options = {}) => {
  const {page = 1, pageSize = 20} = options;
  for (const [name, value] of [['page', page], ['pageSize', pageSize]]) {
    if (!Number.isSafeInteger(value) || value <= 0) {
      throw new RangeError(`${name} must be a positive safe integer`);
    }
  }
  const filtered = exports.filterItems(items, options);
  const total = filtered.length;
  // Compare pages before multiplying to keep very large valid pages safe.
  const start = page > Math.ceil(total / pageSize) ? total : (page - 1) * pageSize;
  return {items: filtered.slice(start, start + pageSize), total};
};
