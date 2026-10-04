function positiveInteger(value, name, fallback) {
  if (value === undefined) return fallback;
  const parsed = typeof value === "string" && /^\d+$/.test(value)
    ? Number(value)
    : value;
  if (typeof parsed !== "number" || !Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new RangeError(`${name} must be a positive safe integer`);
  }
  return parsed;
}

function normalizeOptions(options = {}) {
  if (options === null || typeof options !== "object" || Array.isArray(options)) {
    throw new TypeError("options must be an object");
  }
  return {
    category: options.category,
    page: positiveInteger(options.page, "page", 1),
    pageSize: positiveInteger(options.pageSize, "pageSize", 10),
  };
}

function filterItems(items, options) {
  const { category } = normalizeOptions(options);
  return category === undefined
    ? items.slice()
    : items.filter(item => item.category === category);
}

function query(items, options) {
  const { page, pageSize } = normalizeOptions(options);
  const matched = filterItems(items, options);
  const start = (page - 1) * pageSize;
  return {
    items: start >= matched.length ? [] : matched.slice(start, start + pageSize),
    total: matched.length,
  };
}

exports.query = query;
exports.filterItems = filterItems;
