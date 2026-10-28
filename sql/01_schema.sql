/* =====================================================================
   01_schema.sql  ·  Tienda de ropa (estilo Nike) · SQL Server
   Modelo relacional normalizado (3FN) con 10 entidades.
   ===================================================================== */

IF DB_ID('TiendaRopa') IS NULL
    CREATE DATABASE TiendaRopa;
GO
USE TiendaRopa;
GO

/* 1. MARCAS: una marca vende muchos productos (1:N).
      Separarla evita repetir el nombre de la marca en cada producto. */
CREATE TABLE marcas (
    marca_id     INT IDENTITY(1,1) PRIMARY KEY,
    nombre       NVARCHAR(100) NOT NULL UNIQUE,
    pais_origen  NVARCHAR(60)  NULL
);

/* 2. CATEGORIAS: jerarquía con auto-relación (categoria_padre_id).
      Ej.: Ropa > Calzado > Running. */
CREATE TABLE categorias (
    categoria_id        INT IDENTITY(1,1) PRIMARY KEY,
    nombre              NVARCHAR(100) NOT NULL UNIQUE,
    categoria_padre_id  INT NULL REFERENCES categorias(categoria_id)
);

/* 3. PRODUCTOS: el modelo "padre" de lo que se vende (ej. "Air Zoom Pegasus").
      Tiene marca y categoría (N:1 cada una). */
CREATE TABLE productos (
    producto_id   INT IDENTITY(1,1) PRIMARY KEY,
    marca_id      INT NOT NULL REFERENCES marcas(marca_id),
    categoria_id  INT NOT NULL REFERENCES categorias(categoria_id),
    nombre        NVARCHAR(150) NOT NULL,
    descripcion   NVARCHAR(1000) NULL,
    precio_base   DECIMAL(10,2) NOT NULL CHECK (precio_base >= 0),
    activo        BIT NOT NULL DEFAULT 1,
    creado_en     DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

/* 4. VARIANTES: cada talla + color de un producto es un SKU distinto con su stock.
      Aquí está la clave del negocio: el inventario se controla por variante. */
CREATE TABLE variantes (
    variante_id  INT IDENTITY(1,1) PRIMARY KEY,
    producto_id  INT NOT NULL REFERENCES productos(producto_id),
    sku          NVARCHAR(40)  NOT NULL UNIQUE,
    talla        NVARCHAR(10)  NOT NULL,
    color        NVARCHAR(40)  NOT NULL,
    stock        INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    CONSTRAINT uq_variante UNIQUE (producto_id, talla, color)
);

/* 5. CLIENTES: personas que compran. El email es único (no hay dos cuentas iguales). */
CREATE TABLE clientes (
    cliente_id      INT IDENTITY(1,1) PRIMARY KEY,
    nombre          NVARCHAR(100) NOT NULL,
    email           NVARCHAR(150) NOT NULL UNIQUE,
    telefono        NVARCHAR(20)  NULL,
    fecha_registro  DATE NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE)
);

/* 6. DIRECCIONES: un cliente puede tener varias (1:N).
      Se separa de clientes para no repetir datos de envío en cada pedido. */
CREATE TABLE direcciones (
    direccion_id   INT IDENTITY(1,1) PRIMARY KEY,
    cliente_id     INT NOT NULL REFERENCES clientes(cliente_id),
    ciudad         NVARCHAR(80)  NOT NULL,
    calle          NVARCHAR(150) NOT NULL,
    codigo_postal  NVARCHAR(10)  NULL,
    es_principal   BIT NOT NULL DEFAULT 0
);

/* 7. PEDIDOS: cabecera de la compra (quién, cuándo, a dónde, estado, total). */
CREATE TABLE pedidos (
    pedido_id     INT IDENTITY(1,1) PRIMARY KEY,
    cliente_id    INT NOT NULL REFERENCES clientes(cliente_id),
    direccion_id  INT NOT NULL REFERENCES direcciones(direccion_id),
    fecha         DATETIME2 NOT NULL,
    estado        NVARCHAR(20) NOT NULL
                  CHECK (estado IN ('pendiente','pagado','enviado','entregado','cancelado')),
    total         DECIMAL(10,2) NOT NULL CHECK (total >= 0)
);

/* 8. DETALLE_PEDIDO: líneas del pedido. Relación N:M entre pedidos y variantes.
      precio_unitario se guarda aquí (snapshot): si el precio cambia mañana,
      el pedido de hoy conserva el precio que pagó el cliente. */
CREATE TABLE detalle_pedido (
    detalle_id       INT IDENTITY(1,1) PRIMARY KEY,
    pedido_id        INT NOT NULL REFERENCES pedidos(pedido_id),
    variante_id      INT NOT NULL REFERENCES variantes(variante_id),
    cantidad         INT NOT NULL CHECK (cantidad > 0),
    precio_unitario  DECIMAL(10,2) NOT NULL CHECK (precio_unitario >= 0)
);

/* 9. PAGOS: un pedido puede tener uno o más pagos (1:N), p. ej. pago parcial. */
CREATE TABLE pagos (
    pago_id    INT IDENTITY(1,1) PRIMARY KEY,
    pedido_id  INT NOT NULL REFERENCES pedidos(pedido_id),
    metodo     NVARCHAR(20) NOT NULL
               CHECK (metodo IN ('tarjeta','paypal','transferencia','efectivo')),
    monto      DECIMAL(10,2) NOT NULL CHECK (monto >= 0),
    fecha      DATETIME2 NOT NULL
);

/* 10. RESENAS: calificación de un cliente a un producto.
       Restricción: un cliente solo puede reseñar cada producto una vez. */
CREATE TABLE resenas (
    resena_id     INT IDENTITY(1,1) PRIMARY KEY,
    producto_id   INT NOT NULL REFERENCES productos(producto_id),
    cliente_id    INT NOT NULL REFERENCES clientes(cliente_id),
    calificacion  TINYINT NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
    comentario    NVARCHAR(500) NULL,
    fecha         DATETIME2 NOT NULL,
    CONSTRAINT uq_resena UNIQUE (producto_id, cliente_id)
);
GO

/* Verificación rápida: deben aparecer las 10 tablas */
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
