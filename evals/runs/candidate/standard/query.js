function positiveInteger(value, fallback, name) {
  if (value === undefined) return fallback;
  const number = typeof value === 'number' ? value
    : typeof value === 'string' && /^\d+$/.test(value) ? Number(value) : NaN;
  if (!Number.isSafeInteger(number) || number <= 0) {
    throw new RangeError(`${name} must be a positive safe integer`);
  }
  return number;
}

function filterItems(items, options = {}) {
  return options.category === undefined
    ? items.slice()
    : items.filter(item => item.category === options.category);
}

function query(items, options = {}) {
  const page = positiveInteger(options.page, 1, 'page');
  const pageSize = positiveInteger(options.pageSize, 10, 'pageSize');
  const filtered = filterItems(items, options);
  const total = filtered.length;
  const start = page > Math.ceil(total / pageSize) ? total : (page - 1) * pageSize;
  return {items: filtered.slice(start, start + pageSize), total};
}

exports.filterItems = filterItems;
exports.query = query;
