function escapeField(value) {
  const text = String(value);
  return /[,"\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

exports.csv = items => 'id,name,price\n' + items
  .map(item => [item.id, item.name, item.price].map(escapeField).join(','))
  .join('\n');
