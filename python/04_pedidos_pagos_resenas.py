import pyodbc
import random
from faker import Faker
from datetime import datetime, date

CONN_STR = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=TiendaRopa;Trusted_Connection=yes;TrustServerCertificate=yes;"

fake = Faker('es_MX')
Faker.seed(42)
random.seed(42)

def conectar():
    return pyodbc.connect(CONN_STR)

def limpiar(cursor):
    tablas = ['resenas', 'pagos', 'detalle_pedido', 'pedidos']
    for tabla in tablas:
        cursor.execute(f"DELETE FROM {tabla}")
        cursor.execute(f"DBCC CHECKIDENT ('{tabla}', RESEED, 0)")

def cargar_catalogo(cursor):
    cursor.execute("SELECT cliente_id, fecha_registro FROM clientes")
    clientes = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT direccion_id, cliente_id FROM direcciones")
    direcciones = {}
    for row in cursor.fetchall():
        direcciones.setdefault(row[1], []).append(row[0])
        
    cursor.execute("""
        SELECT v.variante_id, v.producto_id, CAST(p.precio_base AS FLOAT)
        FROM variantes v 
        JOIN productos p ON v.producto_id = p.producto_id
    """)
    variantes = [{"variante_id": row[0], "producto_id": row[1], "precio": float(row[2])} for row in cursor.fetchall()]
    
    return clientes, direcciones, variantes

def insertar_en_lotes(cursor, query, datos, tamaño_lote=500):
    for i in range(0, len(datos), tamaño_lote):
        cursor.executemany(query, datos[i:i+tamaño_lote])

def poblar_pedidos(cursor, clientes, direcciones, variantes):
    detalles_data = []
    pagos_data = []
    compras_historicas = []
    
    estados_probabilidad = (['entregado'] * 70) + (['enviado'] * 15) + (['pagado'] * 8) + (['pendiente'] * 4) + (['cancelado'] * 3)
    metodos_pago = ['tarjeta', 'paypal', 'transferencia', 'efectivo']

    for _ in range(1500):
        cliente_id = random.choice(list(clientes.keys()))
        fecha_reg = clientes[cliente_id]
        
        if isinstance(fecha_reg, date) and not isinstance(fecha_reg, datetime):
            fecha_reg = datetime.combine(fecha_reg, datetime.min.time())
            
        direccion_id = random.choice(direcciones[cliente_id])
        fecha_pedido = fake.date_time_between_dates(datetime_start=fecha_reg, datetime_end=datetime.now())
        estado = random.choice(estados_probabilidad)
        
        num_lineas = random.randint(1, 4)
        variantes_elegidas = random.sample(variantes, num_lineas)
        
        total_pedido = 0
        lineas_temp = []
        for v in variantes_elegidas:
            cantidad = random.randint(1, 3)
            precio_hist = v['precio']
            total_pedido += cantidad * precio_hist
            lineas_temp.append((v['variante_id'], v['producto_id'], cantidad, precio_hist))
            

        cursor.execute("""
            INSERT INTO pedidos (cliente_id, direccion_id, fecha, estado, total)
            OUTPUT INSERTED.pedido_id
            VALUES (?, ?, ?, ?, ?)
        """, (cliente_id, direccion_id, fecha_pedido, estado, total_pedido))
        
        pedido_id = int(cursor.fetchone()[0])
        
        for var_id, prod_id, cant, precio in lineas_temp:
            detalles_data.append((pedido_id, var_id, cant, precio))
            compras_historicas.append((cliente_id, prod_id, fecha_pedido))
            
        if estado in ['pagado', 'enviado', 'entregado']:
            fecha_pago = fake.date_time_between_dates(datetime_start=fecha_pedido, datetime_end=datetime.now())
            pagos_data.append((pedido_id, random.choice(metodos_pago), total_pedido, fecha_pago))
            
    return detalles_data, pagos_data, compras_historicas

def poblar_detalle(cursor, detalles_data):
    query = "INSERT INTO detalle_pedido (pedido_id, variante_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)"
    insertar_en_lotes(cursor, query, detalles_data)

def poblar_pagos(cursor, pagos_data):
    query = "INSERT INTO pagos (pedido_id, metodo, monto, fecha) VALUES (?, ?, ?, ?)"
    insertar_en_lotes(cursor, query, pagos_data)

def poblar_resenas(cursor, compras_historicas):
    compras_unicas = {}
    for cliente_id, producto_id, fecha_compra in compras_historicas:
        clave = (cliente_id, producto_id)
        if clave not in compras_unicas or fecha_compra < compras_unicas[clave]:
            compras_unicas[clave] = fecha_compra
            
    muestras = random.sample(list(compras_unicas.items()), min(600, len(compras_unicas)))
    resenas_data = []
    
    for (cliente_id, producto_id), fecha_compra in muestras:
        calificacion = random.randint(1, 5)
        comentario = None if random.random() < 0.30 else fake.sentence()
        fecha_resena = fake.date_time_between_dates(datetime_start=fecha_compra, datetime_end=datetime.now())
        resenas_data.append((producto_id, cliente_id, calificacion, comentario, fecha_resena))
        
    query = "INSERT INTO resenas (producto_id, cliente_id, calificacion, comentario, fecha) VALUES (?, ?, ?, ?, ?)"
    insertar_en_lotes(cursor, query, resenas_data)

def main():
    conn = conectar()
    cursor = conn.cursor()
    try:
        limpiar(cursor)
        clientes, direcciones, variantes = cargar_catalogo(cursor)
        
        detalles_data, pagos_data, compras_historicas = poblar_pedidos(cursor, clientes, direcciones, variantes)
        poblar_detalle(cursor, detalles_data)
        poblar_pagos(cursor, pagos_data)
        poblar_resenas(cursor, compras_historicas)
        
        conn.commit()
        print("Población transaccional (pedidos, detalles, pagos y reseñas) ejecutada exitosamente.")
    except Exception as e:
        conn.rollback()
        print(f"Error detectado, realizando rollback: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()