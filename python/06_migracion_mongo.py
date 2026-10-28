import pyodbc
from pymongo import MongoClient, ASCENDING
from bson.decimal128 import Decimal128
from collections import defaultdict
from datetime import date, datetime

# Configuración de conexiones / Connection configuration
SQL_CONN_STR = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=TiendaRopa;Trusted_Connection=yes;TrustServerCertificate=yes;"
MONGO_URI = "mongodb://localhost:27017/"

def conectar_sql():
    return pyodbc.connect(SQL_CONN_STR)

def conectar_mongo():
    cliente = MongoClient(MONGO_URI)
    return cliente["TiendaRopa"]

def convertir_fecha(val):
    """Convierte un objeto datetime.date a datetime.datetime para compatibilidad con BSON/MongoDB."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime.combine(val, datetime.min.time())
    return val

# --- FUNCIONES DE CARGA Y AGRUPACIÓN / LOADING AND GROUPING FUNCTIONS ---

def cargar_marcas(cursor):
    cursor.execute("SELECT marca_id, nombre, pais_origen FROM marcas ORDER BY marca_id")
    return {row[0]: {"marca_id": row[0], "nombre": row[1], "pais_origen": row[2]} for row in cursor.fetchall()}

def cargar_variantes(cursor):
    cursor.execute("SELECT variante_id, producto_id, sku, talla, color, stock FROM variantes ORDER BY variante_id")
    variantes_por_prod = defaultdict(list)
    for row in cursor.fetchall():
        variantes_por_prod[row[1]].append({
            "variante_id": row[0], "sku": row[2], "talla": row[3], "color": row[4], "stock": row[5]
        })
    return variantes_por_prod

def cargar_direcciones(cursor):
    cursor.execute("SELECT direccion_id, cliente_id, ciudad, calle, codigo_postal, es_principal FROM direcciones ORDER BY direccion_id")
    dir_por_cliente = defaultdict(list)
    for row in cursor.fetchall():
        dir_por_cliente[row[1]].append({
            "direccion_id": row[0], "ciudad": row[2], "calle": row[3], 
            "codigo_postal": row[4], "es_principal": bool(row[5])
        })
    return dir_por_cliente

def cargar_detalles(cursor):
    query = """
        SELECT d.pedido_id, d.variante_id, v.sku, p.nombre AS nombre_producto, 
               v.talla, v.color, d.cantidad, d.precio_unitario
        FROM detalle_pedido d
        JOIN variantes v ON d.variante_id = v.variante_id
        JOIN productos p ON v.producto_id = p.producto_id
        ORDER BY d.detalle_id
    """
    cursor.execute(query)
    detalles_por_pedido = defaultdict(list)
    for row in cursor.fetchall():
        detalles_por_pedido[row[0]].append({
            "variante_id": row[1], "sku": row[2], "nombre_producto": row[3],
            "talla": row[4], "color": row[5], "cantidad": row[6],
            "precio_unitario": Decimal128(str(row[7]))
        })
    return detalles_por_pedido

def cargar_pagos(cursor):
    cursor.execute("SELECT pago_id, pedido_id, metodo, monto, fecha FROM pagos ORDER BY pago_id")
    pagos_por_pedido = defaultdict(list)
    for row in cursor.fetchall():
        pagos_por_pedido[row[1]].append({
            "metodo": row[2], 
            "monto": Decimal128(str(row[3])), 
            "fecha": convertir_fecha(row[4])
        })
    return pagos_por_pedido

# --- FUNCIONES DE MIGRACIÓN / MIGRATION FUNCTIONS ---

def migrar_categorias(cursor, db_mongo):
    cursor.execute("SELECT categoria_id, nombre, categoria_padre_id FROM categorias ORDER BY categoria_id")
    docs = [{"_id": row[0], "nombre": row[1], "categoria_padre_id": row[2]} for row in cursor.fetchall()]
    if docs: db_mongo.categorias.insert_many(docs)

def migrar_productos(cursor, db_mongo, marcas, variantes):
    cursor.execute("SELECT producto_id, marca_id, categoria_id, nombre, descripcion, precio_base, activo, creado_en FROM productos ORDER BY producto_id")
    docs = []
    for row in cursor.fetchall():
        prod_id = row[0]
        docs.append({
            "_id": prod_id,
            "categoria_id": row[2],
            "nombre": row[3],
            "descripcion": row[4],
            "precio_base": Decimal128(str(row[5])),
            "activo": bool(row[6]),
            "creado_en": convertir_fecha(row[7]),
            "marca": marcas.get(row[1]),
            "variantes": variantes.get(prod_id, [])
        })
    for i in range(0, len(docs), 500):
        db_mongo.productos.insert_many(docs[i:i+500])

def migrar_clientes(cursor, db_mongo, direcciones):
    cursor.execute("SELECT cliente_id, nombre, email, telefono, fecha_registro FROM clientes ORDER BY cliente_id")
    docs = []
    for row in cursor.fetchall():
        cli_id = row[0]
        docs.append({
            "_id": cli_id, 
            "nombre": row[1], 
            "email": row[2], 
            "telefono": row[3], 
            "fecha_registro": convertir_fecha(row[4]),
            "direcciones": direcciones.get(cli_id, [])
        })
    for i in range(0, len(docs), 500):
        db_mongo.clientes.insert_many(docs[i:i+500])

def migrar_pedidos(cursor, db_mongo, detalles, pagos):
    query = """
        SELECT p.pedido_id, p.cliente_id, p.fecha, p.estado, p.total, 
               d.ciudad, d.calle, d.codigo_postal
        FROM pedidos p
        JOIN direcciones d ON p.direccion_id = d.direccion_id
        ORDER BY p.pedido_id
    """
    cursor.execute(query)
    docs = []
    for row in cursor.fetchall():
        ped_id = row[0]
        docs.append({
            "_id": ped_id, 
            "cliente_id": row[1], 
            "fecha": convertir_fecha(row[2]), 
            "estado": row[3], 
            "total": Decimal128(str(row[4])),
            "envio": {"ciudad": row[5], "calle": row[6], "codigo_postal": row[7]},
            "items": detalles.get(ped_id, []),
            "pagos": pagos.get(ped_id, [])
        })
    for i in range(0, len(docs), 500):
        db_mongo.pedidos.insert_many(docs[i:i+500])

def migrar_resenas(cursor, db_mongo):
    cursor.execute("SELECT resena_id, producto_id, cliente_id, calificacion, comentario, fecha FROM resenas ORDER BY resena_id")
    docs = [{
        "_id": row[0], 
        "producto_id": row[1], 
        "cliente_id": row[2], 
        "calificacion": row[3], 
        "comentario": row[4], 
        "fecha": convertir_fecha(row[5])
    } for row in cursor.fetchall()]
    for i in range(0, len(docs), 500):
        db_mongo.resenas.insert_many(docs[i:i+500])

def crear_indices(db_mongo):
    db_mongo.clientes.create_index([("email", ASCENDING)], unique=True)
    db_mongo.productos.create_index([("variantes.sku", ASCENDING)])
    db_mongo.pedidos.create_index([("cliente_id", ASCENDING)])
    db_mongo.resenas.create_index([("producto_id", ASCENDING)])
    db_mongo.resenas.create_index([("cliente_id", ASCENDING)])

def main():
    sql_conn = conectar_sql()
    cursor = sql_conn.cursor()
    db_mongo = conectar_mongo()

    try:
        print("Limpiando colecciones en MongoDB (Idempotencia / Idempotency)...")
        for col in ["categorias", "productos", "clientes", "pedidos", "resenas"]:
            db_mongo[col].drop()

        print("Cargando relaciones en memoria / Loading relations into memory...")
        marcas = cargar_marcas(cursor)
        variantes = cargar_variantes(cursor)
        direcciones = cargar_direcciones(cursor)
        detalles = cargar_detalles(cursor)
        pagos = cargar_pagos(cursor)

        print("Migrando colecciones / Migrating collections...")
        migrar_categorias(cursor, db_mongo)
        migrar_productos(cursor, db_mongo, marcas, variantes)
        migrar_clientes(cursor, db_mongo, direcciones)
        migrar_pedidos(cursor, db_mongo, detalles, pagos)
        migrar_resenas(cursor, db_mongo)
        
        print("Creando índices / Creating indexes...")
        crear_indices(db_mongo)

        print("Migración a MongoDB ejecutada exitosamente / MongoDB migration executed successfully.")
    except Exception as e:
        print(f"Error detectado durante la migración / Error detected during migration: {e}")
    finally:
        sql_conn.close()

if __name__ == "__main__":
    main()