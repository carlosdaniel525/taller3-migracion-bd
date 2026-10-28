

IF DB_ID('TiendaRopa') IS NULL
    CREATE DATABASE TiendaRopa;
GO
USE TiendaRopa;
GO

CREATE TABLE marcas (
    marca_id     INT IDENTITY(1,1) PRIMARY KEY,
    nombre       NVARCHAR(100) NOT NULL UNIQUE,
    pais_origen  NVARCHAR(60)  NULL
);

CREATE TABLE categorias (
    categoria_id        INT IDENTITY(1,1) PRIMARY KEY,
    nombre              NVARCHAR(100) NOT NULL UNIQUE,
    categoria_padre_id  INT NULL REFERENCES categorias(categoria_id)
);

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

CREATE TABLE variantes (
    variante_id  INT IDENTITY(1,1) PRIMARY KEY,
    producto_id  INT NOT NULL REFERENCES productos(producto_id),
    sku          NVARCHAR(40)  NOT NULL UNIQUE,
    talla        NVARCHAR(10)  NOT NULL,
    color        NVARCHAR(40)  NOT NULL,
    stock        INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    CONSTRAINT uq_variante UNIQUE (producto_id, talla, color)
);

CREATE TABLE clientes (
    cliente_id      INT IDENTITY(1,1) PRIMARY KEY,
    nombre          NVARCHAR(100) NOT NULL,
    email           NVARCHAR(150) NOT NULL UNIQUE,
    telefono        NVARCHAR(20)  NULL,
    fecha_registro  DATE NOT NULL DEFAULT CAST(SYSDATETIME() AS DATE)
);

CREATE TABLE direcciones (
    direccion_id   INT IDENTITY(1,1) PRIMARY KEY,
    cliente_id     INT NOT NULL REFERENCES clientes(cliente_id),
    ciudad         NVARCHAR(80)  NOT NULL,
    calle          NVARCHAR(150) NOT NULL,
    codigo_postal  NVARCHAR(10)  NULL,
    es_principal   BIT NOT NULL DEFAULT 0
);

CREATE TABLE pedidos (
    pedido_id     INT IDENTITY(1,1) PRIMARY KEY,
    cliente_id    INT NOT NULL REFERENCES clientes(cliente_id),
    direccion_id  INT NOT NULL REFERENCES direcciones(direccion_id),
    fecha         DATETIME2 NOT NULL,
    estado        NVARCHAR(20) NOT NULL
                  CHECK (estado IN ('pendiente','pagado','enviado','entregado','cancelado')),
    total         DECIMAL(10,2) NOT NULL CHECK (total >= 0)
);

CREATE TABLE detalle_pedido (
    detalle_id       INT IDENTITY(1,1) PRIMARY KEY,
    pedido_id        INT NOT NULL REFERENCES pedidos(pedido_id),
    variante_id      INT NOT NULL REFERENCES variantes(variante_id),
    cantidad         INT NOT NULL CHECK (cantidad > 0),
    precio_unitario  DECIMAL(10,2) NOT NULL CHECK (precio_unitario >= 0)
);

CREATE TABLE pagos (
    pago_id    INT IDENTITY(1,1) PRIMARY KEY,
    pedido_id  INT NOT NULL REFERENCES pedidos(pedido_id),
    metodo     NVARCHAR(20) NOT NULL
               CHECK (metodo IN ('tarjeta','paypal','transferencia','efectivo')),
    monto      DECIMAL(10,2) NOT NULL CHECK (monto >= 0),
    fecha      DATETIME2 NOT NULL
);

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

SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
