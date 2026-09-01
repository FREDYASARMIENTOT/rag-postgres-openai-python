"""
Servidor MCP para el RAG Institucional — Universidad del Rosario.

Propósito:
    Expone las capacidades del RAG Institucional como herramientas MCP
    que un agente IA puede consumir. MCP es la UNICA interfaz entre
    el agente y el RAG.

Contexto arquitectónico:
    Agente IA (MCP Client)
        │ MCP (stdio)
        ▼
    MCP Server UR (ESTE MODULO)
        │
        ├── cargar_contenido_rag
        ├── consultar_rag_institucional
        └── obtener_documento_rag
        │
        ▼
    RAG (servicios internos)
        │
        ▼
    PostgreSQL + pgvector + Foundry

    PRINCIPIOS:
    1. El agente NO accede directamente a PostgreSQL.
    2. El agente NO genera embeddings.
    3. MCP es la UNICA interfaz del agente con el RAG.

SEGURIDAD:
    - NO expone SQL, comandos, filesystem, python_eval.
    - Entradas validadas antes de procesar.
    - Secretos desde variables de entorno (nunca expuestos).

TRANSPORTE:
    - Desarrollo: stdio.
    - Futuro: Streamable HTTP en Azure.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from mcp.server.mcpserver import MCPServer

from fastapi_app.servicio_ingesta import ServicioIngesta
from fastapi_app.servicio_retrieval import ServicioRetrieval
from fastapi_app.repositorio_documentos import RepositorioDocumentos

logger = logging.getLogger("ragapp")


# =============================================================================
# LÍMITES DE SEGURIDAD
# =============================================================================

TAMANO_MAXIMO_CONTENIDO = int(os.getenv("MCP_MAX_CONTENT_SIZE", "102400"))
LIMITE_MAXIMO_RESULTADOS = int(os.getenv("MCP_MAX_RESULTS", "50"))

TIPO_DOCUMENTO_PERMITIDOS = frozenset({
    "facultad", "reglamento", "resolucion", "acuerdo",
    "circular", "directriz", "informe", "manual",
    "guia", "formato", "general",
})


def _validar_tipo_documento(tipo: str) -> str:
    """Valida tipo contra lista blanca. Usa 'general' como fallback seguro."""
    tipo = tipo.strip().lower()
    if tipo in TIPO_DOCUMENTO_PERMITIDOS:
        return tipo
    logger.warning("Tipo no permitido: '%s'. Usando 'general'.", tipo)
    return "general"


def _validar_limite(limite: Any) -> int:
    """Acota límite entre 1 y LIMITE_MAXIMO_RESULTADOS."""
    try:
        return max(1, min(int(limite), LIMITE_MAXIMO_RESULTADOS))
    except (TypeError, ValueError):
        return 10


def crear_mcp_servidor(
    repositorio: RepositorioDocumentos,
    servicio_ingesta: ServicioIngesta,
    servicio_retrieval: ServicioRetrieval,
    nombre: str = "UR-RAG-MCP-Server",
) -> MCPServer:
    """Crea servidor MCP con herramientas del RAG Institucional.

    Inyecta dependencias de negocio para permitir tests con mocks.

    Args:
        repositorio: Repositorio de documentos.
        servicio_ingesta: Servicio de ingestión.
        servicio_retrieval: Servicio de búsqueda.
        nombre: Nombre del servidor.

    Returns:
        MCPServer configurado.
    """
    mcp = MCPServer(nombre)

    # =========================================================================
    # HERRAMIENTA 1: cargar_contenido_rag
    # =========================================================================

    @mcp.tool()
    async def cargar_contenido_rag(
        titulo: str,
        contenido: str,
        fuente: str = "",
        tipo_documento: str = "general",
        metadata: Optional[str] = None,
    ) -> dict:
        """Carga nuevo contenido al RAG Institucional de la Universidad del Rosario.

        El documento se fragmenta, se generan embeddings y se almacena
        en PostgreSQL + pgvector para búsqueda semántica posterior.

        Args:
            titulo: Título descriptivo del documento.
            contenido: Contenido en Markdown o texto plano.
            fuente: Origen institucional (URL, dependencia).
            tipo_documento: Clasificación permitida.
            metadata: JSON opcional con metadatos.

        Returns:
            Dict: documento_id, titulo, cantidad_fragmentos, estado, fuente.

        Raises:
            ValueError: Validaciones de entrada.
        """
        # Validar tamaño
        if len(contenido) > TAMANO_MAXIMO_CONTENIDO:
            raise ValueError(
                f"Contenido excede máximo de {TAMANO_MAXIMO_CONTENIDO} "
                f"caracteres (recibido: {len(contenido)})."
            )

        tipo_valido = _validar_tipo_documento(tipo_documento)

        # Parsear metadata JSON
        metadata_dict: Optional[dict] = None
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
                if not isinstance(metadata_dict, dict):
                    raise ValueError("metadata debe ser un objeto JSON.")
            except json.JSONDecodeError as e:
                raise ValueError(f"metadata JSON inválido: {e}")

        resultado = await servicio_ingesta.ingestar(
            titulo=titulo, contenido=contenido,
            fuente=fuente, tipo_documento=tipo_valido,
            metadatos=metadata_dict,
        )
        return resultado.to_dict()

    # =========================================================================
    # HERRAMIENTA 2: consultar_rag_institucional
    # =========================================================================

    @mcp.tool()
    async def consultar_rag_institucional(
        consulta: str,
        limite: int = 10,
    ) -> list[dict]:
        """Consulta el RAG Institucional de la Universidad del Rosario.

        Busca fragmentos de documentos relevantes para la consulta
        usando búsqueda semántica vectorial (text-embedding-3-small, 1536d).

        Args:
            consulta: Pregunta o frase en lenguaje natural.
            limite: Número máximo de resultados (1-50, default: 10).

        Returns:
            Lista de resultados con: contenido, documento_id, titulo,
            fuente, score, metadata. Ordenados por relevancia.
            Score: distancia coseno (0 = idéntico, mayor = menos similar).

        Raises:
            ValueError: Consulta vacía.
        """
        limite_acotado = _validar_limite(limite)

        resultados = await servicio_retrieval.consultar(
            consulta=consulta, limite=limite_acotado,
        )
        return [r.to_dict() for r in resultados]

    # =========================================================================
    # HERRAMIENTA 3: obtener_documento_rag
    # =========================================================================

    @mcp.tool()
    async def obtener_documento_rag(
        documento_id: int,
    ) -> dict:
        """Obtiene un documento completo del RAG Institucional.

        Recupera el documento y todos sus fragmentos por ID.

        Args:
            documento_id: ID numérico del documento.

        Returns:
            Dict con: documento_id, titulo, contenido, fuente,
            tipo_documento, estado, metadata, cantidad_fragmentos,
            fragmentos (lista ordenada).

        Raises:
            ValueError: Si el documento_id no existe.
        """
        if documento_id <= 0:
            raise ValueError(f"documento_id debe ser positivo: {documento_id}")

        resultado = await servicio_retrieval.obtener_documento_completo(documento_id)
        if resultado is None:
            raise ValueError(f"Documento con id {documento_id} no encontrado.")
        return resultado

    return mcp