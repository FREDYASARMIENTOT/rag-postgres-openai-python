"""
Modelo de datos institucional para el RAG — Universidad del Rosario.
FASE F: Modelo de Datos Institucional RAG + LOG

Proposito:
    Punto de entrada unificado para todos los modelos SQLAlchemy del RAG
    Institucional. Importa y re-exporta modelos normalizados de los schemas
    rag (conocimiento documental) y log (trazabilidad operacional).

Schemas:
    rag  -> Series documentales, temas, periodos, documentos, fragmentos,
            embeddings vectoriales (VECTOR(3072)), clasificacion tematica.
    log  -> Cargas, consultas, documentos recuperados, fragmentos recuperados,
            eventos de auditoria.

Legacy:
    Los modelos legacy (public.documentos, public.fragmentos_documento) se
    mantienen en modelos_institucionales_legacy.py para compatibilidad.
"""

from fastapi_app.modelos_rag_catalogo import SerieDocumental, Tema, Periodo  # noqa: F401
from fastapi_app.modelos_rag_documentos import Documento  # noqa: F401
from fastapi_app.modelos_rag_clasificacion import DocumentoTema, FragmentoDocumento  # noqa: F401
from fastapi_app.modelos_log import CargaDocumento, Consulta  # noqa: F401
from fastapi_app.modelos_log_consultas import ConsultaDocumento, ConsultaFragmento, EventoDocumento  # noqa: F401