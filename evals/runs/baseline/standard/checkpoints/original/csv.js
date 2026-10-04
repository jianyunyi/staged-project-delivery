exports.csv = (items) => "id,name,price\n" + items.map(x=>`${x.id},${x.name},${x.price}`).join("\n");
