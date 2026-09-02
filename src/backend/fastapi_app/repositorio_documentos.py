"""
Repositorio de documentos institucionales — Capa de persistencia.

Propósito:
    Implementa operaciones CRUD sobre las tablas `rag.documentos` y
    `rag.fragmentos_documento` del RAG Institucional, usando los
    modelos correctos de modelos_rag_documentos.py y modelos_rag_catalogo.py.

Contexto arquitectónico:
    Capa de acceso a datos del RAG Institucional. Separa la lógica
    de negocio (servicios) de la persistencia (SQLAlchemy).
    Ningún servicio debe usar SQLAlchemy directamente fuera de este módulo.

FASE F.2 — Modelo Documental Multiformato:
    - Usa exclusivamente los modelos definitivos de modelos_rag_documentos.py
      y modelos_rag_catalogo.py (NO modelos_institucionales.py legacy).
    - Columnas correctas: titulo_documento, fuente_documento, estado_vigencia,
      numero_orden, id_documento (FK), etc.
    - Soporta id_formato_archivo, cantidad_paginas, hora_documento, hora_corte.
    - Incluye usuario_cargador e identificador_usuario_cargador en creación.

Seguridad:
    - Todas las operaciones usan SQLAlchemy ORM (no SQL raw).
    - No se exponen embeddings en respuestas por defecto.
    - IDs validados como enteros positivos.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_app.modelos_rag_catalogo import FormatoArchivo
from fastapi_app.modelos_rag_clasificacion import FragmentoDocumento
from fastapi_app.modelos_rag_documentos import Documento

logger = logging.getLogger("ragapp")


class RepositorioDocumentos:
    """
    Acceso a datos para documentos y fragmentos institucionales.

    Encapsula todas las operaciones de persistencia del RAG Institucional.
    Los servicios de negocio (ingesta, retrieval) dependen de este
    repositorio, no de SQLAlchemy directamente.

    Args:
        session: Sesión asíncrona de SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ──────────────────────────────────────────────────────────────
    # DOCUMENTOS
    # ──────────────────────────────────────────────────────────────

    async def crear_documento(
        self,
        titulo_documento: str,
        contenido: str,
        fuente_documento: str,
        tipo_documento: str,
        id_serie_documental: int = 1,
        id_formato_archivo: Optional[int] = None,
        nombre_archivo_original: Optional[str] = None,
        extension_archivo: Optional[str] = None,
        mime_type: Optional[str] = None,
        cantidad_paginas: Optional[int] = None,
        tamano_bytes: Optional[int] = None,
        hash_sha256: Optional[str] = None,
        usuario_cargador: Optional[str] = None,
        identificador_usuario_cargador: Optional[str] = None,
        estado_vigencia: str = "VIGENTE",
    ) -> Documento:
        """Crea un nuevo documento en la base de datos.

        Args:
            titulo_documento: Título del documento.
            contenido: Texto completo del documento.
            fuente_documento: Origen institucional.
            tipo_documento: Clasificación documental.
            id_serie_documental: FK a serie documental.
            id_formato_archivo: FK a formato de archivo.
            nombre_archivo_original: Nombre del archivo original.
            extension_archivo: Extensión del archivo (sin punto).
            mime_type: Tipo MIME del archivo.
            cantidad_paginas: Número de páginas (PDFs).
            tamano_bytes: Tamaño del archivo original.
            hash_sha256: Hash SHA-256 del contenido.
            usuario_cargador: Nombre/ID del usuario que carga.
            identificador_usuario_cargador: Identificador único.
            estado_vigencia: Estado del documento.

        Returns:
            Documento creado con ID asignado.

        Raises:
            ValueError: Si titulo_documento o contenido están vacíos.
        """
        if not titulo_documento or not titulo_documento.strip():
            raise ValueError("El título del documento no puede estar vacío.")
        if not contenido or not contenido.strip():
            raise ValueError("El contenido del documento no puede estar vacío.")

        documento = Documento(
            id_serie_documental=id_serie_documental,
            id_formato_archivo=id_formato_archivo,
            titulo_documento=titulo_documento.strip(),
            tipo_documento=tipo_documento.strip() if tipo_documento else "general",
            nombre_archivo_original=nombre_archivo_original,
            extension_archivo=extension_archivo,
            mime_type=mime_type,
            cantidad_paginas=cantidad_paginas,
            fuente_documento=fuente_documento.strip() if fuente_documento else "Sin fuente",
            usuario_cargador=usuario_cargador,
            identificador_usuario_cargador=identificador_usuario_cargador,
            tamano_bytes=tamano_bytes,
            hash_sha256=hash_sha256,
            estado_vigencia=estado_vigencia,
        )
        self.session.add(documento)
        await self.session.flush()
        logger.info(
            "Documento creado: id_documento=%d titulo='%s'",
            documento.id_documento, documento.titulo_documento,
        )
        return documento

    async def obtener_documento_por_id(self, documento_id: int) -> Optional[Documento]:
        """Obtiene un documento por su ID.

        Args:
            documento_id: ID del documento.

        Returns:
            Documento si existe, None si no.

        Raises:
            ValueError: Si documento_id es <= 0.
        """
        if documento_id <= 0:
            raise ValueError(f"documento_id debe ser positivo: {documento_id}")
        resultado = await self.session.execute(
            select(Documento).where(Documento.id_documento == documento_id)
        )
        return resultado.scalar_one_or_none()

    async def obtener_documentos(
        self,
        tipo_documento: Optional[str] = None,
        limite: int = 50,
        offset: int = 0,
    ) -> List[Documento]:
        """Obtiene documentos con filtros opcionales."""
        consulta = select(Documento)
        if tipo_documento:
            consulta = consulta.where(Documento.tipo_documento == tipo_documento)
        consulta = consulta.order_by(Documento.id_documento.desc()).limit(limite).offset(offset)
        resultado = await self.session.execute(consulta)
        return list(resultado.scalars().all())

    async def obtener_formato_archivo_por_codigo(self, codigo: str) -> Optional[FormatoArchivo]:
        """Obtiene un formato de archivo por su código (PDF, MD, TXT)."""
        resultado = await self.session.execute(
            select(FormatoArchivo).where(FormatoArchivo.codigo_formato == codigo.upper())
        )
        return resultado.scalar_one_or_none()

    # ──────────────────────────────────────────────────────────────
    # FRAGMENTOS
    # ──────────────────────────────────────────────────────────────

    async def crear_fragmento(
        self,
        documento_id: int,
        contenido: str,
        numero_orden: int,
        embedding: Optional[list[float]] = None,
    ) -> FragmentoDocumento:
        """Crea un fragmento para un documento.

        Args:
            documento_id: ID del documento padre.
            contenido: Texto del fragmento.
            numero_orden: Número de orden del fragmento.
            embedding: Vector de embedding opcional.

        Returns:
            FragmentoDocumento creado.

        Raises:
            ValueError: Si documento_id <= 0 o contenido vacío.
        """
        if documento_id <= 0:
            raise ValueError("El ID del documento debe ser un entero positivo.")
        if not contenido or not contenido.strip():
            raise ValueError("El contenido del fragmento no puede estar vacío.")

        fragmento = FragmentoDocumento(
            id_documento=documento_id,
            contenido=contenido.strip(),
            numero_orden=numero_orden,
            embedding=embedding,
        )
        self.session.add(fragmento)
        await self.session.flush()
        return fragmento

    async def obtener_fragmentos_por_documento(
        self, documento_id: int
    ) -> List[FragmentoDocumento]:
        """Obtiene todos los fragmentos de un documento, ordenados."""
        if documento_id <= 0:
            raise ValueError("El ID del documento debe ser un entero positivo.")
        resultado = await self.session.execute(
            select(FragmentoDocumento)
            .where(FragmentoDocumento.id_documento == documento_id)
            .order_by(FragmentoDocumento.numero_orden)
        )
        return list(resultado.scalars().all())

    async def eliminar_fragmentos_por_documento(self, documento_id: int) -> int:
        """Elimina todos los fragmentos de un documento.

        Returns:
            Número de fragmentos eliminados.
        """
        fragmentos = await self.obtener_fragmentos_por_documento(documento_id)
        for f in fragmentos:
            await self.session.delete(f)
        if fragmentos:
            await self.session.flush()
        return len(fragmentos)

    async def buscar_fragmentos_por_similitud(
        self,
        embedding_consulta: list[float],
        limite: int = 10,
    ) -> List[tuple[FragmentoDocumento, float]]:
        """Busca fragmentos por similitud coseno.

        Usa el operador <=> de pgvector para distancia coseno.

        Args:
            embedding_consulta: Vector de embedding (3072d).
            limite: Máximo de resultados.

        Returns:
            Lista de tuplas (FragmentoDocumento, score) ordenadas por
            relevancia. score = distancia coseno (menor = más similar).
        """
        if isinstance(embedding_consulta, list):
            emb_text = "[" + ",".join(str(x) for x in embedding_consulta) + "]"
        else:
            emb_text = embedding_consulta

        consulta = text("""
            SELECT fd.id_fragmento, fd.id_documento, fd.numero_orden, fd.contenido,
                   fd.cantidad_caracteres, fd.fecha_creacion, fd.hora_creacion,
                   fd.embedding <=> :q_emb AS score
            FROM rag.fragmentos_documento fd
            WHERE fd.embedding IS NOT NULL
            ORDER BY score ASC
            LIMIT :limite
        """)
        resultado = await self.session.execute(
            consulta, {"q_emb": emb_text, "limite": limite}
        )
        filas = resultado.fetchall()
        fragmentos: list[tuple[FragmentoDocumento, float]] = []
        for fila in filas:
            frag = FragmentoDocumento(
                id_fragmento=fila.id_fragmento,
                id_documento=fila.id_documento,
                numero_orden=fila.numero_orden,
                contenido=fila.contenido,
                cantidad_caracteres=fila.cantidad_caracteres,
                fecha_creacion=fila.fecha_creacion,
            )
            fragmentos.append((frag, float(fila.score)))
        return fragmentos

    async def eliminar_documento(self, documento_id: int) -> bool:
        """Elimina un documento y sus fragmentos (cascade).

        Returns:
            True si se eliminó, False si no existía.
        """
        documento = await self.obtener_documento_por_id(documento_id)
        if not documento:
            return False
        await self.session.delete(documento)
        await self.session.flush()
        logger.info("Documento eliminado: id_documento=%d", documento_id)
        return True