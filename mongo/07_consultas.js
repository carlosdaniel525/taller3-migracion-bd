

use TiendaRopa;

printjson(db.productos.aggregate([
  { $group: { _id: "$nombre", n: { $sum: 1 } } },
  { $match: { n: { $gt: 1 } } }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  { $unwind: "$items" },
  {
    $group: {
      _id: {
        sku: "$items.sku",
        producto: "$items.nombre_producto",
        talla: "$items.talla",
        color: "$items.color"
      },
      totalUnidades: { $sum: "$items.cantidad" }
    }
  },
  { $sort: { totalUnidades: -1 } },
  { $limit: 10 },
  {
    $project: {
      _id: 0,
      sku: "$_id.sku",
      producto: "$_id.producto",
      talla: "$_id.talla",
      color: "$_id.color",
      totalUnidades: 1
    }
  }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  { $unwind: "$items" },
  {
    $lookup: {
      from: "productos",
      let: { itemSku: "$items.sku" },
      pipeline: [
        { $match: { $expr: { $in: ["$$itemSku", "$variantes.sku"] } } }
      ],
      as: "producto_info"
    }
  },
  { $unwind: "$producto_info" },
  {
    $group: {
      _id: "$producto_info.marca.nombre",
      ingresosTotales: { $sum: { $multiply: ["$items.cantidad", "$items.precio_unitario"] } }
    }
  },
  { $sort: { ingresosTotales: -1 } },
  { $project: { _id: 0, marca: "$_id", ingresosTotales: 1 } }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  {
    $group: {
      _id: "$cliente_id",
      gastoTotal: { $sum: "$total" },
      totalPedidos: { $sum: 1 }
    }
  },
  { $sort: { gastoTotal: -1 } },
  { $limit: 10 },
  {
    $lookup: {
      from: "clientes",
      localField: "_id",
      foreignField: "_id",
      as: "cliente_info"
    }
  },
  { $unwind: "$cliente_info" },
  {
    $project: {
      _id: 0,
      cliente_id: "$_id",
      nombreCliente: "$cliente_info.nombre",
      gastoTotal: 1,
      totalPedidos: 1
    }
  }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  {
    $group: {
      _id: { año: { $year: "$fecha" }, mes: { $month: "$fecha" } },
      totalPedidos: { $sum: 1 },
      ingresosMensuales: { $sum: "$total" }
    }
  },
  { $sort: { "_id.año": 1, "_id.mes": 1 } },
  {
    $project: {
      _id: 0,
      año: "$_id.año",
      mes: "$_id.mes",
      totalPedidos: 1,
      ingresosMensuales: 1
    }
  }
]).toArray());

printjson(db.resenas.aggregate([
  {
    $group: {
      _id: "$producto_id",
      promedioCalificacion: { $avg: "$calificacion" },
      totalResenas: { $sum: 1 }
    }
  },
  { $match: { totalResenas: { $gte: 3 } } },
  { $sort: { promedioCalificacion: 1 } },
  { $limit: 5 },
  {
    $lookup: {
      from: "productos",
      localField: "_id",
      foreignField: "_id",
      as: "producto_info"
    }
  },
  { $unwind: "$producto_info" },
  {
    $project: {
      _id: 0,
      producto_id: "$_id",
      nombreProducto: "$producto_info.nombre",
      promedioCalificacion: 1,
      totalResenas: 1
    }
  }
]).toArray());

printjson(db.pedidos.aggregate([
  { $unwind: "$pagos" },
  {
    $group: {
      _id: "$pagos.metodo",
      cantidadPagos: { $sum: 1 },
      montoTotal: { $sum: "$pagos.monto" }
    }
  },
  { $sort: { montoTotal: -1 } },
  { $project: { _id: 0, metodoPago: "$_id", cantidadPagos: 1, montoTotal: 1 } }
]).toArray());

printjson(db.productos.aggregate([
  { $unwind: "$variantes" },
  { $match: { "variantes.stock": { $lt: 5 } } },
  {
    $lookup: {
      from: "categorias",
      localField: "categoria_id",
      foreignField: "_id",
      as: "categoria_info"
    }
  },
  { $unwind: "$categoria_info" },
  {
    $project: {
      _id: 0,
      productoId: "$_id",
      nombreProducto: "$nombre",
      categoria: "$categoria_info.nombre",
      sku: "$variantes.sku",
      talla: "$variantes.talla",
      color: "$variantes.color",
      stock: "$variantes.stock"
    }
  }
]).toArray());

printjson(db.pedidos.aggregate([
  { $match: { estado: { $ne: "cancelado" } } },
  { $unwind: "$items" },
  {
    $group: {
      _id: null,
      unidades: { $sum: "$items.cantidad" },
      ingresos: { $sum: { $multiply: ["$items.cantidad", "$items.precio_unitario"] } }
    }
  }
]).toArray());