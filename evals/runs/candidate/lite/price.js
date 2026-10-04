exports.formatPrice = function(value) {
  if (value == null || Number.isNaN(value)) return "—";
  return Number(value).toFixed(2);
};
