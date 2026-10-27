CREATE TABLE comprobantes (
 document_id VARCHAR(64) PRIMARY KEY,
 fingerprint VARCHAR(64) NOT NULL,
 revision VARCHAR(64) NOT NULL,
 ruc_emisor VARCHAR(11) NOT NULL,
 cliente VARCHAR(200) NOT NULL,
 fecha DATE NOT NULL,
 serie VARCHAR(4) NOT NULL,
 numero VARCHAR(8) NOT NULL,
 subtotal DECIMAL(25,2) NOT NULL,
 igv DECIMAL(25,2) NOT NULL,
 total DECIMAL(25,2) NOT NULL,
 estado VARCHAR(20) NOT NULL,
 creado_en VARCHAR(40) NOT NULL,
 actualizado_en VARCHAR(40) NOT NULL,
 error VARCHAR(2000),
 payload CLOB NOT NULL,
 CONSTRAINT uq_comprobante UNIQUE (ruc_emisor, serie, numero)
);
CREATE INDEX ix_comprobantes_estado ON comprobantes(estado);
CREATE TABLE comprobante_items (
 document_id VARCHAR(64) NOT NULL REFERENCES comprobantes(document_id),
 posicion INT NOT NULL,
 descripcion VARCHAR(200) NOT NULL,
 cantidad DECIMAL(12,3) NOT NULL,
 precio_unitario DECIMAL(15,2) NOT NULL,
 PRIMARY KEY(document_id, posicion)
);
CREATE TABLE comprobante_eventos (
 document_id VARCHAR(64) NOT NULL REFERENCES comprobantes(document_id),
 posicion INT NOT NULL,
 estado VARCHAR(20) NOT NULL,
 fecha VARCHAR(40) NOT NULL,
 detalle VARCHAR(2000) NOT NULL,
 PRIMARY KEY(document_id, posicion)
);
CREATE TABLE comprobante_archivos (
 document_id VARCHAR(64) NOT NULL REFERENCES comprobantes(document_id),
 extension VARCHAR(3) NOT NULL CHECK(extension IN ('xml','pdf')),
 contenido BLOB NOT NULL,
 PRIMARY KEY(document_id, extension)
);
