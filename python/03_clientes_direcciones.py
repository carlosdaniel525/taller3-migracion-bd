import pyodbc
import random
from faker import Faker

# Configuración de conexión idéntica al paso anterior
CONN_STR = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=TiendaRopa;Trusted_Connection=yes;TrustServerCertificate=yes;"

fake = Faker('es_MX')
Faker.seed(42)
random.seed(42)

def conectar():
    return pyodbc.connect(CONN_STR)

def limpiar(cursor):
    # Idempotencia: Borrar en orden inverso a las dependencias de llaves foráneas
    tablas = ['direcciones', 'clientes']
    for tabla in tablas:
        cursor.execute(f"DELETE FROM {tabla}")
        # Reiniciar contador a 0 para que los IDs comiencen exactamente en 1
        cursor.execute(f"DBCC CHECKIDENT ('{tabla}', RESEED, 0)")

def poblar_clientes(cursor):
    clientes_data = []
    
    for _ in range(800):
        nombre = fake.name()
        email = fake.unique.ascii_free_email()
        telefono = None if random.random() < 0.20 else fake.phone_number()[:20]
        fecha_registro = fake.date_between(start_date='-3y', end_date='today')
        
        clientes_data.append((nombre, email, telefono, fecha_registro))
        
    # Inserción masiva en bloque (batch insert)
    cursor.executemany("""
        INSERT INTO clientes (nombre, email, telefono, fecha_registro) 
        VALUES (?, ?, ?, ?)
    """, clientes_data)
    
    # Consultar los IDs reales (actual IDs) generados directamente desde la tabla
    cursor.execute("SELECT cliente_id FROM clientes")
    
    # Retornar una lista (list) con los IDs extraídos de las filas (rows)
    return [row[0] for row in cursor.fetchall()]

def poblar_direcciones(cursor, clientes_ids):
    direcciones_data = []
    
    for cliente_id in clientes_ids:
        # Cada cliente tiene entre 1 y 3 direcciones
        num_direcciones = random.randint(1, 3)
        for i in range(num_direcciones):
            ciudad = fake.city()[:80]
            calle = fake.street_address()[:150]
            cp = fake.postcode()[:10]
            
            # Solo la primera dirección generada para el cliente será la principal
            es_principal = 1 if i == 0 else 0
            
            direcciones_data.append((cliente_id, ciudad, calle, cp, es_principal))
            
    # Inserción masiva de direcciones
    cursor.executemany("""
        INSERT INTO direcciones (cliente_id, ciudad, calle, codigo_postal, es_principal)
        VALUES (?, ?, ?, ?, ?)
    """, direcciones_data)

def main():
    conn = conectar()
    cursor = conn.cursor()
    try:
        limpiar(cursor)
        clientes_ids = poblar_clientes(cursor)
        poblar_direcciones(cursor, clientes_ids)
        conn.commit()
        print("Población de clientes y direcciones ejecutada exitosamente.")
    except Exception as e:
        conn.rollback()
        print(f"Error detectado, realizando rollback: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
