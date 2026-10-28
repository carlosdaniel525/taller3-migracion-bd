# Taller 3 · Migración de una tienda de ropa: SQL Server → MongoDB

Proyecto de **Bases de datos II**. Se modela una tienda de ropa al estilo Nike en SQL Server (10 tablas, 11.230 registros), se migra a MongoDB con Python y se responde a preguntas de negocio con consultas de agregación.

## Orden de ejecución

| Paso | Archivo | Qué hace | Dónde se ejecuta |
|---|---|---|---|
| 1 | `sql/01_schema.sql` | Crea la base `TiendaRopa` y sus 10 tablas | SSMS |
| 2 | `python/02_catalogo.py` | Marcas, categorías, productos y variantes | Python |
| 3 | `python/03_clientes_direcciones.py` | 800 clientes y 1.635 direcciones | Python |
| 4 | `python/04_pedidos_pagos_resenas.py` | 1.500 pedidos, 3.769 líneas, 1.401 pagos y 600 reseñas | Python |
| 5 | `sql/05_verificacion.sql` | Comprobaciones de integridad en SQL Server | SSMS |
| 6 | `python/06_migracion_mongo.py` | Migra a MongoDB con documentos embebidos | Python |
| 7 | `mongo/05_verificacion.js` | Comprobaciones de la migración | mongosh |
| 8 | `mongo/07_consultas.js` | 8 consultas de agregación de negocio | mongosh |

## Requisitos

- SQL Server (Express sirve) con ODBC Driver 18 for SQL Server
- MongoDB Community (servicio corriendo en `localhost:27017`)
- Python 3.10+ y `pip install -r requirements.txt`
- mongosh (o MongoDB Compass)

## Cómo ejecutar

```powershell
# SQL Server: ejecutar sql/01_schema.sql en SSMS
python python/03_clientes_direcciones.py
python python/04_pedidos_pagos_resenas.py
python python/06_migracion_mongo.py
mongosh < mongo/05_verificacion.js
mongosh < mongo/07_consultas.js
```

## Resultados verificados

| Dato | SQL Server | MongoDB |
|---|---|---|
| Suma de totales de pedidos | 756.367,39 | 756.367,39 |
| Unidades (no cancelados) | 7.326 | 7.326 |
| Ingresos (no cancelados) | 736.180,65 | 736.180,65 |
| Total de pagos | 703.837,34 | 703.837,34 |

## Decisiones de modelado

Consulta [docs/modelo.md](docs/modelo.md) y la presentación completa en [docs/presentacion.md](docs/presentacion.md).

## Errores documentados

Los errores encontrados durante el desarrollo, su causa y su corrección están en la sección 6 de [docs/presentacion.md](docs/presentacion.md).

## Errores conocidos (pendientes de corregir)

Estos puntos se detectaron en la revisión final. El código del repositorio es la versión que produjo las cifras verificadas; las correcciones se documentan aquí.

- **E10 · Reseñas de compras canceladas.** `04_pedidos_pagos_resenas.py` agrega `compras_historicas` sin revisar el estado del pedido, así que algunas reseñas pueden venir de pedidos cancelados. Verificación: el bloque 8 de `sql/05_verificacion.sql` debe devolver filas. Corrección propuesta: agregar la compra solo si `estado != 'cancelado'`.
- **E11 · Dinero con `float` en el generador.** Los precios se convierten a `float` en `04_pedidos_pagos_resenas.py`. Las sumas verificadas cuadran, pero lo correcto sería `Decimal`.
- **E12 · Múltiples `$lookup`.** Ninguna consulta de `07_consultas.js` tiene dos `$lookup` encadenados, requisito de la consigna. Corrección propuesta: agregar una consulta de ventas por categoría (productos → categorías).
