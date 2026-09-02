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

import logging
import os
from typing import Any, Optional

from mcp.server.mcpserver import MCPServer

from fastapi_app.servicio_generacion import ServicioGeneracion
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


def _validar_usuario(usuario: str) -> str:
    """Valida que el usuario esté presente y no exceda límites."""
    if not usuario or not usuario.strip():
        raise ValueError("El parámetro 'usuario' es obligatorio para esta operación.")
    usuario = usuario.strip()
    if len(usuario) > 200:
        logger.warning("usuario truncado de %d a 200 caracteres", len(usuario))
        usuario = usuario[:200]
    return usuario


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
    servicio_generacion: Optional[ServicioGeneracion] = None,
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
        contenido: str,
        usuario: str,
        fuente: str = "sin fuente",
        tipo_documento: str = "general",
    ) -> dict:
        """Carga contenido en el RAG Institucional de la Universidad del Rosario.

        Divide el contenido en fragmentos, genera embeddings y persiste.
        El tipo de documento se usa para indexar y filtrar (facultad, reglamento, etc).
        El usuario es obligatorio para trazabilidad.

        Args:
            contenido: Texto completo a cargar en el RAG.
            usuario: Nombre o identificador del usuario que realiza la carga.
            fuente: Origen institucional del contenido.
            tipo_documento: Tipo documental (facultad, reglamento, resolucion,
                           acuerdo, circular, directriz, informe, manual,
                           guia, formato, general). Default: 'general'.

        Returns:
            Dict con: documento_id, titulo, cantidad_fragmentos, estado, fuente.

        Raises:
            ValueError: Contenido vacío o usuario no proporcionado.
        """
        tipo_valido = _validar_tipo_documento(tipo_documento)
        usuario_validado = _validar_usuario(usuario)

        if not contenido or not contenido.strip():
            raise ValueError("El contenido no puede estar vacío.")

        if len(contenido) > TAMANO_MAXIMO_CONTENIDO:
            raise ValueError(
                f"Contenido excede máximo de {TAMANO_MAXIMO_CONTENIDO} "
                f"caracteres (recibido: {len(contenido)})."
            )

        # Primeras 100 líneas como título
        lineas = contenido.strip().split("\n")
        titulo = lineas[0].strip()[:200]
        if not titulo:
            titulo = f"Documento {tipo_valido} - {fuente}"

        resultado = await servicio_ingesta.ingestar(
            titulo=titulo, contenido=contenido,
            fuente=fuente, tipo_documento=tipo_valido,
            usuario_cargador=usuario_validado,
        )
        logger.info(
            "Carga exitosa: id=%d tipo=%s frags=%d usuario=%s",
            resultado.documento_id, tipo_valido, resultado.cantidad_fragmentos,
            usuario_validado,
        )
        return resultado.to_dict()

    # =========================================================================
    # HERRAMIENTA 2: consultar_rag_institucional
    # =========================================================================

    @mcp.tool()
    async def consultar_rag_institucional(
        consulta: str,
        usuario: str,
        limite: int = 10,
    ) -> list[dict]:
        """Consulta el RAG Institucional de la Universidad del Rosario.

        Busca fragmentos de documentos relevantes para la consulta
        usando búsqueda semántica vectorial (text-embedding-3-large, 3072d).

        Args:
            consulta: Pregunta o frase en lenguaje natural.
            usuario: Nombre o identificador del usuario que consulta.
            limite: Número máximo de resultados (1-50, default: 10).

        Returns:
            Lista de resultados con: contenido, documento_id, titulo,
            fuente, score. Ordenados por relevancia.
            Score: distancia coseno (0 = idéntico, mayor = menos similar).

        Raises:
            ValueError: Consulta vacía.
        """
        _validar_usuario(usuario)
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
        usuario: str,
    ) -> dict:
        """Obtiene un documento completo del RAG Institucional.

        Recupera el documento y todos sus fragmentos por ID.

        Args:
            documento_id: ID numérico del documento.
            usuario: Nombre o identificador del usuario que consulta.

        Returns:
            Dict con: documento_id, titulo, fuente,
            tipo_documento, estado, cantidad_fragmentos,
            fragmentos (lista ordenada).

        Raises:
            ValueError: Si el documento_id no existe.
        """
        _validar_usuario(usuario)
        if documento_id <= 0:
            raise ValueError(f"documento_id debe ser positivo: {documento_id}")

        resultado = await servicio_retrieval.obtener_documento_completo(documento_id)
        if resultado is None:
            raise ValueError(f"Documento con id {documento_id} no encontrado.")
        return resultado

    # =========================================================================
    # HERRAMIENTA 4: consultar_rag_con_generacion (si servicio_generacion esta disponible)
    # =========================================================================

    if servicio_generacion:

        @mcp.tool()
        async def consultar_rag_con_generacion(
            consulta: str,
            usuario: str,
            limite: int = 5,
        ) -> dict:
            """Consulta el RAG Institucional y genera una respuesta fundamentada.

            Realiza busqueda semantica sobre los documentos institucionales y
            genera una respuesta utilizando GPT-5.6 Luna (ur-rag-gpt-5-6-luna)
            fundamentada exclusivamente en los fragmentos recuperados.

            Args:
                consulta: Pregunta en lenguaje natural.
                usuario: Nombre o identificador del usuario que consulta.
                limite: Numero maximo de fragmentos a recuperar (1-10, default: 5).

            Returns:
                Dict con: consulta, respuesta, fragmentos_count, deployment,
                modelo, fragmentos (contenido, score, titulo, fuente).
            """
            _validar_usuario(usuario)
            limite_acotado = max(1, min(int(limite), 10))

            resultado = await servicio_generacion.consultar_con_generacion(
                consulta=consulta, limite=limite_acotado,
            )
            return resultado.to_dict()

    return mcp