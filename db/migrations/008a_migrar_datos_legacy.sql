-- =============================================================================
-- MIGRACION 008a: Migrar datos de public.documentos a rag.documentos
-- FASE F: Modelo de Datos Institucional RAG + LOG
-- =============================================================================
-- IMPORTANTE:
--   NO elimina tablas legacy.
--   NO usa DELETE, TRUNCATE, DROP.
--   Conserva IDs originales.
-- =============================================================================

DO $$
DECLARE
    v_serie_id BIGINT;
    v_periodo_id BIGINT;
    v_docs_count INTEGER;
    v_frags_count INTEGER;
    v_emb_count INTEGER;
BEGIN
    -- PASO 1: Serie documental por defecto
    IF NOT EXISTS (SELECT 1 FROM rag.series_documentales WHERE codigo_serie = 'GENERAL') THEN
        INSERT INTO rag.series_documentales (codigo_serie, nombre_serie, descripcion_serie, periodicidad)
        VALUES ('GENERAL', 'General', 'Serie general para documentos no clasificados. Migracion desde legacy.', 'PERMANENTE')
        RETURNING id_serie_documental INTO v_serie_id;
    ELSE
        SELECT id_serie_documental INTO v_serie_id FROM rag.series_documentales WHERE codigo_serie = 'GENERAL';
    END IF;

    -- PASO 2: Periodo por defecto
    IF NOT EXISTS (SELECT 1 FROM rag.periodos WHERE codigo_periodo = 'SIN_PERIODO') THEN
        INSERT INTO rag.periodos (codigo_periodo, tipo_periodo, anio, descripcion_periodo)
        VALUES ('SIN_PERIODO', 'PERMANENTE', EXTRACT(YEAR FROM CURRENT_DATE),
                'Periodo por defecto para documentos migrados sin periodo definido.')
        RETURNING id_periodo INTO v_periodo_id;
    ELSE
        SELECT id_periodo INTO v_periodo_id FROM rag.periodos WHERE codigo_periodo = 'SIN_PERIODO';
    END IF;

    -- PASO 3: Migrar documentos
    INSERT INTO rag.documentos (
        id_serie_documental, id_periodo, titulo_documento, tipo_documento,
        fuente_documento, fecha_carga, hora_carga,
        version_documento, estado_vigencia, participa_retrieval,
        fecha_creacion, hora_creacion
    )
    SELECT
        v_serie_id, v_periodo_id,
        COALESCE(doc.titulo, 'Documento sin titulo'),
        COALESCE(doc.tipo_documento, 'general'),
        COALESCE(doc.fuente, 'Migracion legacy'),
        CURRENT_DATE, CURRENT_TIME,
        1, 'VIGENTE', TRUE,
        CURRENT_DATE, CURRENT_TIME
    FROM public.documentos doc
    WHERE NOT EXISTS (
        SELECT 1 FROM rag.documentos rd
        WHERE rd.titulo_documento = doc.titulo AND rd.fuente_documento = doc.fuente
    );

    GET DIAGNOSTICS v_docs_count = ROW_COUNT;
    RAISE NOTICE 'Documentos migrados: %', v_docs_count;

    -- PASO 4: Migrar fragmentos
    INSERT INTO rag.fragmentos_documento (
        id_documento, numero_orden, contenido, cantidad_caracteres, embedding,
        fecha_creacion, hora_creacion
    )
    SELECT
        rd.id_documento, GREATEST(frag.orden, 1), frag.contenido,
        LENGTH(frag.contenido), frag.embedding,
        CURRENT_DATE, CURRENT_TIME
    FROM public.fragmentos_documento frag
    JOIN public.documentos ld ON ld.id = frag.documento_id
    JOIN rag.documentos rd ON rd.titulo_documento = ld.titulo AND rd.fuente_documento = ld.fuente
    WHERE NOT EXISTS (
        SELECT 1 FROM rag.fragmentos_documento rf
        WHERE rf.id_documento = rd.id_documento AND rf.numero_orden = GREATEST(frag.orden, 1)
    );

    RAISE NOTICE 'Fragmentos migrados: %', v_frags_count;

END;
$$;