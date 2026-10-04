exports.formatPrice = function(value) {
  if (!value) return "—";
  return Number(value).toFixed(2);
};
