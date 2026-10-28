/* =====================================================================
   05_verificacion.sql · Comprobaciones de integridad de TiendaRopa
   Ejecutar en SSMS, base TiendaRopa. Cada bloque indica el resultado esperado.
   ===================================================================== */
USE TiendaRopa;
GO

-- 1. Conteos por tabla (total esperado: 11230)
SELECT 'marcas' AS tabla, COUNT(*) AS total FROM marcas UNION ALL
SELECT 'categorias', COUNT(*) FROM categorias UNION ALL
SELECT 'productos', COUNT(*) FROM productos UNION ALL
SELECT 'variantes', COUNT(*) FROM variantes UNION ALL
SELECT 'clientes', COUNT(*) FROM clientes UNION ALL
SELECT 'direcciones', COUNT(*) FROM direcciones UNION ALL
SELECT 'pedidos', COUNT(*) FROM pedidos UNION ALL
SELECT 'detalle_pedido', COUNT(*) FROM detalle_pedido UNION ALL
SELECT 'pagos', COUNT(*) FROM pagos UNION ALL
SELECT 'resenas', COUNT(*) FROM resenas;

-- 2. Productos sin variantes (0 filas)
SELECT p.producto_id FROM productos p
LEFT JOIN variantes v ON p.producto_id = v.producto_id
WHERE v.variante_id IS NULL;

-- 3. SKU duplicados (0 filas)
SELECT sku, COUNT(*) AS repeticiones FROM variantes GROUP BY sku HAVING COUNT(*) > 1;

-- 4. Clientes sin dirección principal (0 filas)
SELECT c.cliente_id FROM clientes c
WHERE NOT EXISTS (SELECT 1 FROM direcciones d WHERE d.cliente_id = c.cliente_id AND d.es_principal = 1);

-- 5. Dirección de envío que pertenece a otro cliente (0 filas)
SELECT p.pedido_id FROM pedidos p
JOIN direcciones d ON p.direccion_id = d.direccion_id
WHERE d.cliente_id <> p.cliente_id;

-- 6. Pedido cuyo total no coincide con la suma de sus líneas (0 filas)
SELECT p.pedido_id, p.total, SUM(d.cantidad * d.precio_unitario) AS suma_detalles
FROM pedidos p JOIN detalle_pedido d ON p.pedido_id = d.pedido_id
GROUP BY p.pedido_id, p.total
HAVING p.total <> SUM(d.cantidad * d.precio_unitario);

-- 7. Pagos en pedidos cancelados (0 filas)
SELECT pa.pago_id FROM pagos pa
JOIN pedidos p ON pa.pedido_id = p.pedido_id
WHERE p.estado = 'cancelado';

-- 8. Reseña sin compra previa NO cancelada (0 filas)
--    ANTES de corregir E10 esta consulta devuelve filas: es la evidencia del error.
--    DESPUÉS de corregir, debe dar 0 filas.
SELECT r.resena_id, r.cliente_id, r.producto_id
FROM resenas r
WHERE NOT EXISTS (
    SELECT 1 FROM pedidos p
    JOIN detalle_pedido d ON p.pedido_id = d.pedido_id
    JOIN variantes v ON d.variante_id = v.variante_id
    WHERE p.cliente_id = r.cliente_id
      AND v.producto_id = r.producto_id
      AND p.estado <> 'cancelado'
);

-- 9. Reseñas duplicadas por cliente y producto (0 filas)
SELECT producto_id, cliente_id, COUNT(*) AS veces
FROM resenas GROUP BY producto_id, cliente_id HAVING COUNT(*) > 1;

-- 10. Stock negativo (0 filas)
SELECT variante_id, stock FROM variantes WHERE stock < 0;

-- 11. Cifras para comparar con MongoDB
-- Esperado: unidades 7326 · ingresos 736180.65
SELECT SUM(d.cantidad) AS unidades,
       SUM(d.cantidad * d.precio_unitario) AS ingresos
FROM detalle_pedido d JOIN pedidos p ON d.pedido_id = p.pedido_id
WHERE p.estado <> 'cancelado';

-- Esperado: total_pagos 703837.34
SELECT SUM(monto) AS total_pagos FROM pagos;

-- Esperado: suma_total 756367.39
SELECT SUM(total) AS suma_total FROM pedidos;
