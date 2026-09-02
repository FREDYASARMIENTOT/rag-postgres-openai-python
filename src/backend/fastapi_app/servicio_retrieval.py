"""
Servicio de retrieval para el RAG Institucional.

Propósito:
    Orquesta la búsqueda semántica: consulta -> embedding ->
    búsqueda vectorial -> enriquecer -> devolver.

Contexto arquitectónico:
    Conecta compute_text_embedding con el repositorio de documentos.
    Es el punto de entrada para `consultar_rag_institucional` y
    `obtener_documento_rag`.

    Pipeline:
        1. Recibir consulta
        2. Generar embedding
        3. Buscar fragmentos por similitud coseno
        4. Enriquecer con documento padre
        5. Devolver resultados con trazabilidad

Seguridad:
    - No expone embeddings internos.
    - No permite SQL injection.
    - Resultados incluyen fuente para trazabilidad.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi_app.embeddings import compute_text_embedding
from fastapi_app.proveedores import ProveedorEmbeddings
from fastapi_app.repositorio_documentos import RepositorioDocumentos

logger = logging.getLogger("ragapp")


class ResultadoBusqueda:
    """Resultado de búsqueda semántica individual.

    Attributes:
        contenido: Texto del fragmento relevante.
        documento_id: ID del documento origen.
        titulo: Título del documento.
        fuente: Fuente institucional.
        score: Distancia coseno (menor = más similar).
        metadatos: Metadatos del fragmento.
        fragmento_id: ID del fragmento.
    """

    def __init__(
        self,
        contenido: str,
        documento_id: int,
        titulo: str,
        fuente: str,
        score: float,
        metadatos: Optional[str] = None,
        fragmento_id: Optional[int] = None,
    ):
        self.contenido = contenido
        self.documento_id = documento_id
        self.titulo = titulo
        self.fuente = fuente
        self.score = round(score, 4)
        self.metadatos = metadatos
        self.fragmento_id = fragmento_id

    def to_dict(self) -> dict:
        return {
            "contenido": self.contenido,
            "documento_id": self.documento_id,
            "titulo": self.titulo,
            "fuente": self.fuente,
            "score": self.score,
            "metadatos": self.metadatos,
            "fragmento_id": self.fragmento_id,
        }

    def __repr__(self) -> str:
        return f"<ResultadoBusqueda doc={self.documento_id} score={self.score:.4f}>"


class ServicioRetrieval:
    """Búsqueda semántica sobre el RAG Institucional.

    Args:
        repositorio: Repositorio de documentos.
        proveedor_embeddings: Proveedor de embeddings encapsulado.
    """

    def __init__(
        self,
        repositorio: RepositorioDocumentos,
        proveedor_embeddings: Optional[ProveedorEmbeddings] = None,
    ):
        self.repositorio = repositorio
        self.proveedor_embeddings = proveedor_embeddings

    async def consultar(
        self,
        consulta: str,
        limite: int = 10,
    ) -> List[ResultadoBusqueda]:
        """Ejecuta consulta semántica sobre el RAG Institucional.

        Args:
            consulta: Pregunta en lenguaje natural.
            limite: Máximo de resultados (default: 10, max: 50).

        Returns:
            Lista de ResultadoBusqueda ordenados por relevancia.

        Raises:
            ValueError: Consulta vacía.
            RuntimeError: Sin cliente de embeddings.
        """
        if not consulta or not consulta.strip():
            raise ValueError("La consulta no puede estar vacía.")
        if not self.proveedor_embeddings:
            raise RuntimeError(
                "No hay proveedor de embeddings configurado."
            )

        logger.info("Retrieval: consulta='%s' limite=%d", consulta[:100], limite)

        # Paso 1: Embedding de consulta
        embedding = await compute_text_embedding(
            texto_consulta=consulta,
            cliente_openai=self.proveedor_embeddings.cliente,
            modelo_embedding=self.proveedor_embeddings.modelo,
            deployment_embedding=self.proveedor_embeddings.deployment,
            dimensiones_embedding=self.proveedor_embeddings.dimensiones,
        )

        # Paso 2: Búsqueda vectorial
        fragmentos = await self.repositorio.buscar_fragmentos_por_similitud(
            embedding_consulta=embedding, limite=limite,
        )

        # Paso 3: Enriquecer con documento padre
        resultados = []
        for frag, score in fragmentos:
            doc = await self.repositorio.obtener_documento_por_id(frag.id_documento)
            if not doc:
                continue
            resultados.append(ResultadoBusqueda(
                contenido=frag.contenido,
                documento_id=doc.id_documento,
                titulo=doc.titulo_documento,
                fuente=doc.fuente_documento,
                score=score,
                metadatos=None,
                fragmento_id=frag.id_fragmento,
            ))

        logger.info("Retrieval: %d resultados", len(resultados))
        return resultados

    async def obtener_documento_completo(
        self, documento_id: int
    ) -> Optional[dict]:
        """Obtiene un documento completo con fragmentos.

        Args:
            documento_id: ID del documento.

        Returns:
            Dict con datos y fragmentos, o None si no existe.
        """
        doc = await self.repositorio.obtener_documento_por_id(documento_id)
        if not doc:
            return None
        fragmentos = await self.repositorio.obtener_fragmentos_por_documento(documento_id)
        return {
            "documento_id": doc.id_documento,
            "titulo": doc.titulo_documento,
            "fuente": doc.fuente_documento,
            "tipo_documento": doc.tipo_documento,
            "estado": doc.estado_vigencia,
            "nombre_archivo_original": doc.nombre_archivo_original,
            "extension_archivo": doc.extension_archivo,
            "formato_id": doc.id_formato_archivo,
            "cantidad_paginas": doc.cantidad_paginas,
            "cantidad_fragmentos": len(fragmentos),
            "fragmentos": [
                {
                    "id_fragmento": f.id_fragmento,
                    "numero_orden": f.numero_orden,
                    "contenido": f.contenido,
                    "cantidad_caracteres": f.cantidad_caracteres,
                }
                for f in fragmentos
            ],
        }