-- =============================================================================
-- Migración 009b: Agregar columnas a rag.documentos
-- FASE F.2 — Modelo Documental Multiformato
--
-- Propósito:
--     Agregar columnas faltantes al modelo documental para soportar
--     identidad completa del archivo, trazabilidad y formato.
--
-- Columnas agregadas:
--     1. id_formato_archivo: FK al catálogo de formatos
--     2. hora_documento: Hora asociada a la fecha del documento
--     3. hora_corte: Hora asociada a la fecha de corte
--     4. cantidad_paginas: Número de páginas del documento original
--
-- Comportamiento:
--     - No destructivo. No elimina columnas existentes.
--     - id_formato_archivo nullable (documentos existentes sin formato)
--     - hora_documento, hora_corte: completan pares fecha+hora
-- =============================================================================

-- 1. Agregar id_formato_archivo
ALTER TABLE rag.documentos
    ADD COLUMN IF NOT EXISTS id_formato_archivo SMALLINT;

-- 2. Agregar hora_documento (completa fecha_documento)
ALTER TABLE rag.documentos
    ADD COLUMN IF NOT EXISTS hora_documento TIME;

-- 3. Agregar hora_corte (completa fecha_corte)
ALTER TABLE rag.documentos
    ADD COLUMN IF NOT EXISTS hora_corte TIME;

-- 4. Agregar cantidad_paginas
ALTER TABLE rag.documentos
    ADD COLUMN IF NOT EXISTS cantidad_paginas SMALLINT;

-- 5. FK a formatos_archivo
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint
        WHERE conname = 'fk_documento_formato_archivo'
    ) THEN
        ALTER TABLE rag.documentos
            ADD CONSTRAINT fk_documento_formato_archivo
            FOREIGN KEY (id_formato_archivo)
            REFERENCES rag.formatos_archivo (id_formato_archivo)
            ON UPDATE CASCADE
            ON DELETE SET NULL;
    END IF;
END $$;

-- 6. Check constraint para cantidad_paginas
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_constraint
        WHERE conname = 'ck_cantidad_paginas'
    ) THEN
        ALTER TABLE rag.documentos
            ADD CONSTRAINT ck_cantidad_paginas
            CHECK (cantidad_paginas IS NULL OR cantidad_paginas >= 1);
    END IF;
END $$;

-- 7. Índice para búsqueda por formato
CREATE INDEX IF NOT EXISTS ix_documentos_id_formato
    ON rag.documentos (id_formato_archivo)
    WHERE id_formato_archivo IS NOT NULL;

-- =============================================================================
-- COMMENTS — español descriptivo
-- =============================================================================

COMMENT ON COLUMN rag.documentos.id_formato_archivo IS
'Identificador del formato de archivo del documento original. '
'Referencia al catálogo rag.formatos_archivo que define la extensión, '
'MIME type y capacidades de ingesta del formato (PDF, MD, TXT, etc.). '
'Permite distinguir un mismo tipo documental en diferentes formatos. '
'Ejemplo: FACULTADES puede existir como PDF y como MD, con el mismo '
'tipo_documento pero diferente id_formato_archivo.';

COMMENT ON COLUMN rag.documentos.hora_documento IS
'Hora asociada al documento original (fecha_documento). '
'Completa el par (fecha_documento, hora_documento) para trazabilidad '
'temporal precisa del contenido documental. '
'Ejemplo: si fecha_documento = 2026-01-15 y hora_documento = 14:30:00.';

COMMENT ON COLUMN rag.documentos.hora_corte IS
'Hora asociada a la fecha de corte del documento. '
'Completa el par (fecha_corte, hora_corte) para trazabilidad temporal '
'precisa de la información contenida. Útil para documentos que '
'reportan datos a un momento específico del día.';

COMMENT ON COLUMN rag.documentos.cantidad_paginas IS
'Número de páginas del documento original. Aplica especialmente a '
'formatos paginados como PDF. Para formatos continuos (MD, TXT) puede '
'permanecer NULL. Check constraint garantiza valor >= 1 cuando se '
'especifica. Se obtiene automáticamente durante la ingesta.';