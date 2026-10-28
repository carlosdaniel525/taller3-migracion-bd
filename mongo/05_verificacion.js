// =====================================================================
// 05_verificacion.js · Comprobaciones de la migración en MongoDB
// Ejecutar en mongosh:  mongosh < 05_verificacion.js
// Cada bloque indica el resultado esperado (el mismo que en SQL Server).
// =====================================================================
use TiendaRopa;

// 1. Conteos de colecciones (300, 15, 800, 1500, 600)
printjson({
  productos: db.productos.countDocuments(),
  categorias: db.categorias.countDocuments(),
  clientes: db.clientes.countDocuments(),
  pedidos: db.pedidos.countDocuments(),
  resenas: db.resenas.countDocuments()
});

// 2. Embebidos (variantes 1202 · direcciones 1635 · items 3769 · pagos 1401)
printjson(db.productos.aggregate([{ $project: { n: { $size: "$variantes" } } }, { $group: { _id: null, total: { $sum: "$n" } } }]).toArray());
printjson(db.clientes.aggregate([{ $project: { n: { $size: "$direcciones" } } }, { $group: { _id: null, total: { $sum: "$n" } } }]).toArray());
printjson(db.pedidos.aggregate([{ $project: { n: { $size: "$items" } } }, { $group: { _id: null, total: { $sum: "$n" } } }]).toArray());
printjson(db.pedidos.aggregate([{ $unwind: "$pagos" }, { $count: "total" }]).toArray());

// 3. Suma de totales (756367.39)
printjson(db.pedidos.aggregate([{ $group: { _id: null, suma: { $sum: "$total" } } }]).toArray());

// 4. Unidades e ingresos de pedidos no cancelados (7326 · 736180.65)
printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  { $unwind: "$items" },
  { $group: { _id: null, unidades: { $sum: "$items.cantidad" }, ingresos: { $sum: { $multiply: ["$items.cantidad", "$items.precio_unitario"] } } } }
]).toArray());

// 5. Pedidos pagados/enviados/entregados sin pagos (0 resultados)
printjson(db.pedidos.aggregate([
  { $match: { estado: { $in: ["pagado", "enviado", "entregado"] }, pagos: { $size: 0 } } },
  { $count: "sin_pago" }
]).toArray());

// 6. Pedidos cancelados con pagos (0 resultados)
printjson(db.pedidos.aggregate([
  { $match: { estado: "cancelado", pagos: { $ne: [] } } },
  { $count: "cancelados_con_pago" }
]).toArray());

// 7. Clientes sin dirección principal (0 resultados)
printjson(db.clientes.aggregate([
  { $match: { "direcciones.es_principal": { $ne: true } } },
  { $count: "sin_principal" }
]).toArray());

// 8. Índices creados (deben aparecer email único, variantes.sku, cliente_id y producto_id)
printjson({
  clientes: db.clientes.getIndexes().map(i => i.name),
  productos: db.productos.getIndexes().map(i => i.name),
  pedidos: db.pedidos.getIndexes().map(i => i.name),
  resenas: db.resenas.getIndexes().map(i => i.name)
});

// 9. Duplicados de nombre de producto (0 resultados)
printjson(db.productos.aggregate([{ $group: { _id: "$nombre", n: { $sum: 1 } } }, { $match: { n: { $gt: 1 } } }]).toArray());
