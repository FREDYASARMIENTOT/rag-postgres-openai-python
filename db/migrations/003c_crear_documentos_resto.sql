-- =============================================================================
-- MIGRACION 003c: COMMENTS restantes e indices de rag.documentos
-- FASE F: Modelo de Datos Institucional RAG + LOG
-- =============================================================================

COMMENT ON COLUMN rag.documentos.cantidad_consultas IS 'Contador acumulado de cuantas veces este documento ha sido recuperado en consultas RAG. Permite identificar documentos de alta y baja utilizacion.';

COMMENT ON COLUMN rag.documentos.fecha_ultima_consulta IS 'Fecha de la ultima consulta que recupero este documento. NULL si nunca ha sido consultado.';

COMMENT ON COLUMN rag.documentos.hora_ultima_consulta IS 'Hora de la ultima consulta que recupero este documento. Almacenada como TIME.';

COMMENT ON COLUMN rag.documentos.fecha_archivado IS 'Fecha en la que el documento fue archivado (estado ARCHIVADO). NULL si no ha sido archivado.';

COMMENT ON COLUMN rag.documentos.hora_archivado IS 'Hora en la que el documento fue archivado.';

COMMENT ON COLUMN rag.documentos.fecha_creacion IS 'Fecha de creacion del registro documental en el catalogo RAG.';

COMMENT ON COLUMN rag.documentos.hora_creacion IS 'Hora de creacion del registro documental.';

COMMENT ON COLUMN rag.documentos.fecha_actualizacion IS 'Fecha de la ultima actualizacion del registro documental. NULL si nunca ha sido actualizado.';

COMMENT ON COLUMN rag.documentos.hora_actualizacion IS 'Hora de la ultima actualizacion del registro documental.';

-- =============================================================================
-- INDICES rag.documentos
-- =============================================================================

CREATE INDEX IF NOT EXISTS ix_documentos_estado_vigencia ON rag.documentos(estado_vigencia);
COMMENT ON INDEX ix_documentos_estado_vigencia IS 'Indice para filtrar documentos por estado de vigencia. Utilizado en consultas RAG para priorizar documentos vigentes.';

CREATE INDEX IF NOT EXISTS ix_documentos_id_serie ON rag.documentos(id_serie_documental);
COMMENT ON INDEX ix_documentos_id_serie IS 'Indice para busquedas de documentos por serie documental.';

CREATE INDEX IF NOT EXISTS ix_documentos_id_periodo ON rag.documentos(id_periodo);
COMMENT ON INDEX ix_documentos_id_periodo IS 'Indice para busquedas de documentos por periodo. Permite filtrar por periodo temporal.';

CREATE INDEX IF NOT EXISTS ix_documentos_fecha_corte ON rag.documentos(fecha_corte);
COMMENT ON INDEX ix_documentos_fecha_corte IS 'Indice para busquedas por fecha de corte del contenido documental.';

CREATE UNIQUE INDEX IF NOT EXISTS ux_documentos_hash_sha256 ON rag.documentos(hash_sha256) WHERE hash_sha256 IS NOT NULL;
COMMENT ON INDEX ux_documentos_hash_sha256 IS 'Indice unico parcial sobre hash SHA-256 para deteccion de documentos duplicados. Solo indexa documentos con hash no nulo.';