// ==========================================
// TALLER 3: CONSULTAS DE AGREGACIÓN EN MONGODB
// Base de datos: TiendaRopa
// ==========================================
use TiendaRopa;

// ------------------------------------------
// VERIFICACIÓN PREVIA: ¿hay nombres de producto repetidos?
// Si devuelve filas, agrupar por nombre sería incorrecto (ver Consulta 1).
// ------------------------------------------
printjson(db.productos.aggregate([
  { $group: { _id: "$nombre", n: { $sum: 1 } } },
  { $match: { n: { $gt: 1 } } }
]).toArray());

// ------------------------------------------
// Consulta 1: Top 10 variantes más vendidas (producto + talla + color)
// Pregunta de negocio: ¿Qué combinaciones de talla y color se venden más para planear producción?
// Decisión que apoya: cuánto producir de cada talla y color.
// Operadores: $match, $unwind, $group, $sort, $limit, $project
// ------------------------------------------
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

// ------------------------------------------
// Consulta 2: Ingresos por marca, sin pedidos cancelados
// Pregunta de negocio: ¿Qué marcas generan más ingresos para negociar alianzas comerciales?
// Decisión que apoya: qué marcas priorizar en compras y promociones.
// Operadores: $match, $unwind, $lookup con pipeline, $group, $sort, $project
// Nota: las variantes están EMBEBIDAS como arreglo dentro de productos, por eso el
// $lookup necesita pipeline: la condición se evalúa dentro del arreglo con $expr y $in.
// ------------------------------------------
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

// ------------------------------------------
// Consulta 3: Top 10 clientes por gasto total
// Pregunta de negocio: ¿Quiénes son los clientes más valiosos para ofrecerles beneficios?
// Operadores: $match, $group, $sort, $limit, $lookup, $unwind, $project
// ------------------------------------------
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

// ------------------------------------------
// Consulta 4: Tendencia mensual de ventas
// Pregunta de negocio: ¿Cómo evolucionan los ingresos y pedidos mes a mes?
// Decisión que apoya: cuándo reforzar inventario o campañas.
// Operadores: $match, $group, $sort, $project
// Nota: $year y $month usan la zona horaria UTC del servidor.
// ------------------------------------------
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

// ------------------------------------------
// Consulta 5: Top 5 productos peor calificados (mínimo 3 reseñas)
// Pregunta de negocio: ¿Qué productos tienen problemas de calidad percibidos?
// Decisión que apoya: revisar proveedor o retirar el producto.
// Operadores: $group, $match, $sort, $limit, $lookup, $unwind, $project
// ------------------------------------------
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

// ------------------------------------------
// Consulta 6: Métodos de pago más utilizados y montos
// Pregunta de negocio: ¿Qué métodos de pago prefieren los clientes?
// Decisión que apoya: qué pasarelas de pago contratar o promocionar.
// Operadores: $unwind, $group, $sort, $project
// ------------------------------------------
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

// ------------------------------------------
// Consulta 7: Alerta de reabastecimiento (stock menor a 5)
// Pregunta de negocio: ¿Qué tallas y colores están por agotarse?
// Decisión que apoya: qué reabastecer primero.
// Operadores: $unwind, $match, $lookup, $unwind, $project
// ------------------------------------------
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

// ------------------------------------------
// VERIFICACIÓN NUMÉRICA CONTRA SQL SERVER
// Mongo: unidades e ingresos de pedidos no cancelados
// ------------------------------------------
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