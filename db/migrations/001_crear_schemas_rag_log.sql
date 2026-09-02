-- =============================================================================
-- MIGRACION 001: Crear schemas rag y log
-- FASE F: Modelo de Datos Institucional RAG + LOG
-- Universidad del Rosario
-- =============================================================================
-- Propósito:
--   Crear los esquemas separados para conocimiento documental (rag) y
--   trazabilidad operacional (log) del RAG Institucional.
--
-- Contexto arquitectónico:
--   EL RAG Institucional utiliza dos esquemas:
--     rag → Documentación institucional, fragmentos, embeddings, clasificación.
--     log → Cargas, consultas, auditoría, eventos de trazabilidad.
--
--   La separación permite:
--     1. Gobiernos de acceso diferentes (rag: solo aplicaciones; log: auditoría).
--     2. Estrategias de backup independientes (rag más frecuente que log).
--     3. Crecimiento aislado (log puede crecer más rápido que rag).
--     4. Políticas de retención diferentes.
--
--   Ambos esquemas residen en la misma BD (rag_institucional).
--   Ninguno interfiere con el schema public (donde residen las tablas legacy).
--
-- Historial:
--   2026-02-09 - Creación inicial (Fase F)
-- =============================================================================

-- SCHEMA: rag
CREATE SCHEMA IF NOT EXISTS rag;

COMMENT ON SCHEMA rag IS
'Esquema que contiene el conocimiento documental institucional utilizado por el RAG Institucional de la Universidad del Rosario. Este esquema alberga series documentales, temas, periodos, documentos, fragmentos con embeddings vectoriales (text-embedding-3-large, 3072 dimensiones) y la clasificación temática de los documentos. Es la fuente de información primaria para los procesos de Retrieval (búsqueda semántica vectorial) y Generación Aumentada por Recuperación (RAG). Es utilizado exclusivamente por los servicios internos del RAG (consulta MCP, ingesta, retrieval, generación). Su contraparte de trazabilidad operacional reside en el esquema "log". Ninguna aplicación externa debe modificar directamente los datos de este esquema.';

-- SCHEMA: log
CREATE SCHEMA IF NOT EXISTS log;

COMMENT ON SCHEMA log IS
'Esquema que contiene la trazabilidad operacional, auditoría, registro de uso y comportamiento del RAG Institucional de la Universidad del Rosario. Este esquema alberga registros de cargas documentales, consultas realizadas, documentos y fragmentos recuperados, y eventos de auditoría sobre el ciclo de vida documental. Proporciona la información necesaria para análisis de uso, detección de anomalías, cumplimiento normativo y mejora continua del sistema RAG. Su contraparte de contenido documental reside en el esquema "rag". La información de este esquema no debe ser utilizada directamente como fuente de conocimiento para respuestas RAG.';