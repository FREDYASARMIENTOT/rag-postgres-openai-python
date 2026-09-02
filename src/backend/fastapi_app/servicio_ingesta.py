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
        usuario_cargador: Optional[str] = None,
        identificador_usuario_cargador: Optional[str] = None,
        id_formato_archivo: Optional[int] = None,
        nombre_archivo_original: Optional[str] = None,
        extension_archivo: Optional[str] = None,
        mime_type: Optional[str] = None,
        cantidad_paginas: Optional[int] = None,
        tamano_bytes: Optional[int] = None,
        hash_sha256: Optional[str] = None,
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

        # Paso 2: Crear documento con metadatos extendidos
        documento = await self.repositorio.crear_documento(
            titulo_documento=titulo, contenido=contenido,
            fuente_documento=fuente, tipo_documento=tipo_documento,
            id_formato_archivo=id_formato_archivo,
            nombre_archivo_original=nombre_archivo_original,
            extension_archivo=extension_archivo,
            mime_type=mime_type,
            cantidad_paginas=cantidad_paginas,
            tamano_bytes=tamano_bytes,
            hash_sha256=hash_sha256,
            usuario_cargador=usuario_cargador,
            identificador_usuario_cargador=identificador_usuario_cargador,
        )

        try:
            # Paso 3: Fragmentar
            fragmentos = self.fragmentador.fragmentar(contenido)
            logger.info("Doc %d: %d fragmentos", documento.id_documento, len(fragmentos))

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
                    documento_id=documento.id_documento,
                    contenido=frag.contenido,
                    numero_orden=frag.orden,
                    embedding=embedding,
                )

            # Paso 6: Commit
            await self.repositorio.session.commit()

            logger.info("Ingesta OK: doc_id=%d frags=%d", documento.id_documento, len(fragmentos))
            return ResultadoIngesta(
                documento_id=documento.id_documento,
                titulo=documento.titulo_documento,
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
        usuario_cargador: Optional[str] = None,
        identificador_usuario_cargador: Optional[str] = None,
    ) -> ResultadoIngesta:
        """Ingiere un documento desde archivo usando el extractor multiformato.

        Selecciona automáticamente el extractor según la extensión del archivo
        (MD, PDF, TXT) y extrae contenido, metadatos y hash. El nombre del
        archivo (sin extensión) se usa como título del documento.

        Raises:
            FileNotFoundError: Archivo no existe.
            ValueError: Formato no soportado.
        """
        from pathlib import Path
        from fastapi_app.extractor_documentos import extraer_documento

        path = Path(ruta_archivo)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")

        resultado_extraccion = extraer_documento(ruta_archivo)
        if not resultado_extraccion.exito:
            raise ValueError(f"Error extrayendo documento: {resultado_extraccion.error}")

        titulo = path.stem.replace("-", " ").replace("_", " ").title()

        # Obtener formato de archivo desde BD (si existe)
        extension = path.suffix.lower().lstrip(".")
        id_formato = None
        try:
            formato = await self.repositorio.obtener_formato_archivo_por_codigo(extension)
            if formato:
                id_formato = formato.id_formato_archivo
        except Exception as exc:
            # La tabla rag.formatos_archivo puede no existir aún (migración
            # 009a pendiente).  En ese caso, la transacción de la sesión
            # queda abortada: debemos hacer rollback explícito para
            # que la ingesta principal pueda continuar con una transacción
            # limpia.
            logger.info(
                "Formato de archivo no disponible para '%s': %s. "
                "Se omite y se limpia la transacción.",
                extension, exc,
            )
            await self.repositorio.session.rollback()

        return await self.ingestar(
            titulo=titulo, contenido=resultado_extraccion.contenido,
            fuente=fuente, tipo_documento=tipo_documento,
            usuario_cargador=usuario_cargador,
            identificador_usuario_cargador=identificador_usuario_cargador,
            id_formato_archivo=id_formato,
            nombre_archivo_original=path.name,
            extension_archivo=extension,
            mime_type=None,  # Se puede obtener de mimetypes si es necesario
            cantidad_paginas=resultado_extraccion.cantidad_paginas,
            tamano_bytes=resultado_extraccion.tamano_bytes,
            hash_sha256=resultado_extraccion.hash_sha256,
        )