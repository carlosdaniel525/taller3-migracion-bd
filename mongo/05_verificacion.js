

use TiendaRopa;

printjson({
  productos: db.productos.countDocuments(),
  categorias: db.categorias.countDocuments(),
  clientes: db.clientes.countDocuments(),
  pedidos: db.pedidos.countDocuments(),
  resenas: db.resenas.countDocuments()
});

printjson(db.productos.aggregate([{ $project: { n: { $size: "$variantes" } } }, { $group: { _id: null, total: { $sum: "$n" } } }]).toArray());
printjson(db.clientes.aggregate([{ $project: { n: { $size: "$direcciones" } } }, { $group: { _id: null, total: { $sum: "$n" } } }]).toArray());
printjson(db.pedidos.aggregate([{ $project: { n: { $size: "$items" } } }, { $group: { _id: null, total: { $sum: "$n" } } }]).toArray());
printjson(db.pedidos.aggregate([{ $unwind: "$pagos" }, { $count: "total" }]).toArray());

printjson(db.pedidos.aggregate([{ $group: { _id: null, suma: { $sum: "$total" } } }]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  { $unwind: "$items" },
  { $group: { _id: null, unidades: { $sum: "$items.cantidad" }, ingresos: { $sum: { $multiply: ["$items.cantidad", "$items.precio_unitario"] } } } }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $in: ["pagado", "enviado", "entregado"] }, pagos: { $size: 0 } } },
  { $count: "sin_pago" }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: "cancelado", pagos: { $ne: [] } } },
  { $count: "cancelados_con_pago" }
]).toArray());

printjson(db.clientes.aggregate([
  { $match: { "direcciones.es_principal": { $ne: true } } },
  { $count: "sin_principal" }
]).toArray());

printjson({
  clientes: db.clientes.getIndexes().map(i => i.name),
  productos: db.productos.getIndexes().map(i => i.name),
  pedidos: db.pedidos.getIndexes().map(i => i.name),
  resenas: db.resenas.getIndexes().map(i => i.name)
});

printjson(db.productos.aggregate([{ $group: { _id: "$nombre", n: { $sum: 1 } } }, { $match: { n: { $gt: 1 } } }]).toArray());
