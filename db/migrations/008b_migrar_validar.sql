-- =============================================================================
-- MIGRACION 008b: Validacion y eventos post-migracion
-- FASE F: Modelo de Datos Institucional RAG + LOG
-- =============================================================================

DO $$
DECLARE
    v_serie_id BIGINT;
    v_periodo_id BIGINT;
    v_docs_count INTEGER;
    v_frags_count INTEGER;
    v_emb_count INTEGER;
BEGIN
    -- Serie documental por defecto
    SELECT id_serie_documental INTO v_serie_id FROM rag.series_documentales WHERE codigo_serie = 'GENERAL';
    -- Periodo por defecto
    SELECT id_periodo INTO v_periodo_id FROM rag.periodos WHERE codigo_periodo = 'SIN_PERIODO';

    -- PASO 5: Contar embeddings migrados
    SELECT COUNT(*) INTO v_emb_count FROM rag.fragmentos_documento WHERE embedding IS NOT NULL;
    RAISE NOTICE 'Embeddings migrados: %', v_emb_count;

    -- PASO 6: Eventos de migracion
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'log' AND table_name = 'eventos_documentos') THEN
        INSERT INTO log.eventos_documentos (
            id_documento, tipo_evento, descripcion_evento,
            usuario_evento, fecha_evento, hora_evento, datos_evento_json
        )
        SELECT rd.id_documento, 'CARGADO',
               'Documento migrado desde esquema legacy public.documentos.',
               'SISTEMA_MIGRACION', CURRENT_DATE, CURRENT_TIME,
               jsonb_build_object('legacy_id', ld.id, 'tipo', 'migracion_fase_f',
                                  'serie', v_serie_id, 'periodo', v_periodo_id)
        FROM public.documentos ld
        JOIN rag.documentos rd ON rd.titulo_documento = ld.titulo AND rd.fuente_documento = ld.fuente;
    END IF;

    -- PASO 7: Validacion final
    SELECT COUNT(*) INTO v_docs_count FROM rag.documentos;
    SELECT COUNT(*) INTO v_frags_count FROM rag.fragmentos_documento;
    SELECT COUNT(*) INTO v_emb_count FROM rag.fragmentos_documento WHERE embedding IS NOT NULL;

    RAISE NOTICE '--- VALIDACION POST-MIGRACION ---';
    RAISE NOTICE 'Documentos en rag.documentos: %', v_docs_count;
    RAISE NOTICE 'Fragmentos en rag.fragmentos_documento: %', v_frags_count;
    RAISE NOTICE 'Embeddings no nulos: %', v_emb_count;
END;
$$;

-- =============================================================================
-- VALIDACION DE CONTEOS
-- =============================================================================
SELECT
    (SELECT COUNT(*) FROM public.documentos) AS docs_legacy,
    (SELECT COUNT(*) FROM rag.documentos) AS docs_rag,
    (SELECT COUNT(*) FROM public.fragmentos_documento) AS frags_legacy,
    (SELECT COUNT(*) FROM rag.fragmentos_documento) AS frags_rag,
    (SELECT COUNT(*) FROM public.fragmentos_documento WHERE embedding IS NOT NULL) AS emb_legacy,
    (SELECT COUNT(*) FROM rag.fragmentos_documento WHERE embedding IS NOT NULL) AS emb_rag;