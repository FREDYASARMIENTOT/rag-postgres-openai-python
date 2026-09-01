"""
Servicio de ingestión para el RAG Institucional.

Propósito:
    Orquesta el pipeline completo: Markdown -> validar -> fragmentar
    -> embedding -> persistir.

Contexto arquitectónico:
    Conecta el fragmentador, compute_text_embedding (de embeddings.py)
    y el repositorio de documentos. Es el punto de entrada para la
    herramienta MCP `cargar_contenido_rag`.

    Pipeline:
        1. Validar entrada
        2. Crear documento en BD
        3. Fragmentar contenido
        4. Generar embedding por fragmento
        5. Persistir fragmentos
        6. Commit
        7. Devolver resultado

Seguridad:
    - No ejecuta código del documento.
    - No permite SQL injection (usa ORM).
    - No expone secretos en logs.

Restricciones:
    - Embedding generado secuencialmente fragmento por fragmento.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi_app.embeddings import compute_text_embedding
from fastapi_app.fragmentador_documentos import FragmentadorDocumentos
from fastapi_app.proveedores import ProveedorEmbeddings
from fastapi_app.repositorio_documentos import RepositorioDocumentos

logger = logging.getLogger("ragapp")


class ResultadoIngesta:
    """Resultado de una operación de ingestión.

    Attributes:
        documento_id: ID del documento creado.
        titulo: Título del documento.
        cantidad_fragmentos: Fragmentos generados.
        estado: Estado (exitoso, error).
        fuente: Fuente del documento.
        mensaje: Mensaje descriptivo.
    """

    def __init__(
        self,
        documento_id: int,
        titulo: str,
        cantidad_fragmentos: int,
        estado: str = "exitoso",
        fuente: str = "",
        mensaje: str = "",
    ):
        self.documento_id = documento_id
        self.titulo = titulo
        self.cantidad_fragmentos = cantidad_fragmentos
        self.estado = estado
        self.fuente = fuente
        self.mensaje = mensaje

    def to_dict(self) -> dict:
        return {
            "documento_id": self.documento_id,
            "titulo": self.titulo,
            "cantidad_fragmentos": self.cantidad_fragmentos,
            "estado": self.estado,
            "fuente": self.fuente,
            "mensaje": self.mensaje,
        }

    def __repr__(self) -> str:
        return (
            f"<ResultadoIngesta id={self.documento_id} "
            f"fragmentos={self.cantidad_fragmentos}>"
        )


class ServicioIngesta:
    """Orquesta la ingestión de documentos en el RAG Institucional.

    Args:
        repositorio: Repositorio de documentos.
        fragmentador: Fragmentador de documentos Markdown.
        cliente_embeddings: Cliente OpenAI para embeddings.
        modelo_embedding: Modelo de embeddings.
        deployment_embedding: Deployment en Azure/Foundry.
        dimensiones_embedding: Dimensiones del embedding (1536).
    """

    def __init__(
        self,
        repositorio: RepositorioDocumentos,
        fragmentador: Optional[FragmentadorDocumentos] = None,
        proveedor_embeddings: Optional[ProveedorEmbeddings] = None,
    ):
        self.repositorio = repositorio
        self.fragmentador = fragmentador or FragmentadorDocumentos()
        self.proveedor_embeddings = proveedor_embeddings

    async def ingestar(
        self,
        titulo: str,
        contenido: str,
        fuente: str = "",
        tipo_documento: str = "general",
        metadatos: Optional[dict] = None,
    ) -> ResultadoIngesta:
        """Ejecuta el pipeline completo de ingestión.

        Args:
            titulo: Título del documento.
            contenido: Contenido en Markdown o texto plano.
            fuente: Origen institucional.
            tipo_documento: Clasificación.
            metadatos: Metadatos adicionales.

        Returns:
            ResultadoIngesta con estado de la operación.

        Raises:
            ValueError: Parámetros inválidos.
            Exception: Error en embeddings o persistencia.
        """
        # Paso 1: Validar
        if not titulo or not titulo.strip():
            raise ValueError("El título del documento es obligatorio.")
        if not contenido or not contenido.strip():
            raise ValueError("El contenido del documento es obligatorio.")

        logger.info("Ingesta: titulo='%s' tipo='%s'", titulo, tipo_documento)

        # Paso 2: Crear documento
        documento = await self.repositorio.crear_documento(
            titulo=titulo, contenido=contenido,
            fuente=fuente, tipo_documento=tipo_documento,
            metadatos=metadatos,
        )

        try:
            # Paso 3: Fragmentar
            fragmentos = self.fragmentador.fragmentar(contenido)
            logger.info("Doc %d: %d fragmentos", documento.id, len(fragmentos))

            # Paso 4-5: Embeddings y persistencia
            for frag in fragmentos:
                embedding = None
                if self.proveedor_embeddings and self.proveedor_embeddings.cliente:
                    embedding = await compute_text_embedding(
                        texto_consulta=frag.contenido,
                        cliente_openai=self.proveedor_embeddings.cliente,
                        modelo_embedding=self.proveedor_embeddings.modelo,
                        deployment_embedding=self.proveedor_embeddings.deployment,
                        dimensiones_embedding=self.proveedor_embeddings.dimensiones,
                    )
                await self.repositorio.crear_fragmento(
                    documento_id=documento.id,
                    contenido=frag.contenido,
                    orden=frag.orden,
                    embedding=embedding,
                    metadatos=frag.metadata,
                )

            # Paso 6: Commit
            await self.repositorio.session.commit()

            logger.info("Ingesta OK: doc_id=%d frags=%d", documento.id, len(fragmentos))
            return ResultadoIngesta(
                documento_id=documento.id,
                titulo=documento.titulo,
                cantidad_fragmentos=len(fragmentos),
                estado="exitoso",
                fuente=fuente,
                mensaje=f"Documento '{titulo}' ingestado con {len(fragmentos)} fragmentos.",
            )

        except Exception as e:
            await self.repositorio.session.rollback()
            logger.error("Error en ingesta '%s': %s", titulo, str(e), exc_info=True)
            raise

    async def ingestar_desde_archivo(
        self,
        ruta_archivo: str,
        fuente: str = "",
        tipo_documento: str = "general",
        metadatos: Optional[dict] = None,
    ) -> ResultadoIngesta:
        """Ingiere un documento desde archivo Markdown.

        El nombre del archivo (sin extensión) se usa como título.

        Raises:
            FileNotFoundError: Archivo no existe.
        """
        import os
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")

        with open(ruta_archivo, "r", encoding="utf-8") as f:
            contenido = f.read()

        titulo = os.path.splitext(os.path.basename(ruta_archivo))[0]
        titulo = titulo.replace("-", " ").replace("_", " ").title()

        return await self.ingestar(
            titulo=titulo, contenido=contenido,
            fuente=fuente, tipo_documento=tipo_documento,
            metadatos=metadatos,
        )