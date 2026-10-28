import pyodbc
import random
from faker import Faker

CONN_STR = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=TiendaRopa;Trusted_Connection=yes;TrustServerCertificate=yes;"

fake = Faker('es_MX')
Faker.seed(42)
random.seed(42)

def conectar():
    return pyodbc.connect(CONN_STR)

def limpiar(cursor):

    tablas = ['variantes', 'productos', 'categorias', 'marcas']
    for tabla in tablas:
        cursor.execute(f"DELETE FROM {tabla}")
        cursor.execute(f"DBCC CHECKIDENT ('{tabla}', RESEED, 0)")

def poblar_marcas(cursor):
    ids = []
    for _ in range(8):

        cursor.execute("INSERT INTO marcas (nombre, pais_origen) OUTPUT INSERTED.marca_id VALUES (?, ?)", 
                       (fake.unique.company(), fake.country()))
        ids.append(cursor.fetchone()[0])
    return ids

def poblar_categorias(cursor):
    ids = []

    for _ in range(5):
        cursor.execute("INSERT INTO categorias (nombre, categoria_padre_id) OUTPUT INSERTED.categoria_id VALUES (?, NULL)", 
                       (fake.unique.word().capitalize(),))
        ids.append(cursor.fetchone()[0])
    

    for _ in range(10):
        cursor.execute("INSERT INTO categorias (nombre, categoria_padre_id) OUTPUT INSERTED.categoria_id VALUES (?, ?)", 
                       (fake.unique.word().capitalize(), random.choice(ids[:5])))
        ids.append(cursor.fetchone()[0])
    return ids

def poblar_productos(cursor, marcas_ids, cat_ids):
    ids = []
    for _ in range(300):
        activo = 1 if random.random() < 0.95 else 0
        precio = round(random.uniform(15.0, 180.0), 2)
        cursor.execute("""
            INSERT INTO productos (marca_id, categoria_id, nombre, descripcion, precio_base, activo) 
            OUTPUT INSERTED.producto_id VALUES (?, ?, ?, ?, ?, ?)""",
            (random.choice(marcas_ids), random.choice(cat_ids), fake.catch_phrase(), fake.sentence(), precio, activo))
        ids.append(cursor.fetchone()[0])
    return ids

def poblar_variantes(cursor, productos_ids):
    tallas = ['XS', 'S', 'M', 'L', 'XL', '38', '39', '40', '41', '42']
    colores = ['Negro', 'Blanco', 'Rojo', 'Azul', 'Gris', 'Verde']
    
    for prod_id in productos_ids:
        num_variantes = random.randint(3, 5)
        combinaciones_usadas = set()
        
        while len(combinaciones_usadas) < num_variantes:
            talla = random.choice(tallas)
            color = random.choice(colores)
            

            if (talla, color) not in combinaciones_usadas:
                combinaciones_usadas.add((talla, color))
                sku = f"PROD-{prod_id}-{talla}-{color}".upper()
                stock = random.randint(0, 80)
                cursor.execute("""
                    INSERT INTO variantes (producto_id, talla, color, sku, stock) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (prod_id, talla, color, sku, stock))

def main():
    conn = conectar()
    cursor = conn.cursor()
    try:
        limpiar(cursor)
        marcas_ids = poblar_marcas(cursor)
        cat_ids = poblar_categorias(cursor)
        prod_ids = poblar_productos(cursor, marcas_ids, cat_ids)
        poblar_variantes(cursor, prod_ids)
        

        conn.commit()
        print("Población de datos (data population) ejecutada exitosamente.")
    except Exception as e:

        conn.rollback()
        print(f"Error detectado, realizando rollback: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()