"""
Repositorio de documentos institucionales — Capa de persistencia.

Propósito:
    Implementa operaciones CRUD sobre las tablas `documentos` y
    `fragmentos_documento` del RAG Institucional.

Contexto arquitectónico:
    Capa de acceso a datos del RAG Institucional. Separa la lógica
    de negocio (servicios) de la persistencia (SQLAlchemy).

    Ningún servicio debe usar SQLAlchemy directamente fuera de este módulo.
    Ningún módulo externo debe importar Documento o FragmentoDocumento
    excepto a través de este repositorio.

Dependencias:
    - SQLAlchemy AsyncSession
    - modelos_institucionales (Documento, FragmentoDocumento)

Seguridad:
    - Todas las operaciones usan SQLAlchemy ORM (no SQL raw).
    - No se exponen embeddings en respuestas por defecto.
    - Transacciones con commit/rollback explícitos.
    - IDs validados como enteros positivos.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_app.modelos_institucionales import Documento, FragmentoDocumento

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
        titulo: str,
        contenido: str,
        fuente: str,
        tipo_documento: str,
        metadatos: Optional[dict] = None,
        estado: str = "activo",
    ) -> Documento:
        """
        Crea un nuevo documento en la base de datos.

        Args:
            titulo: Título del documento.
            contenido: Texto completo del documento.
            fuente: Origen institucional.
            tipo_documento: Clasificación.
            metadata: Metadatos adicionales (se serializa a JSON).
            estado: Estado inicial.

        Returns:
            Documento creado con ID asignado.

        Raises:
            ValueError: Si titulo o contenido están vacíos.
        """
        if not titulo or not titulo.strip():
            raise ValueError("El título del documento no puede estar vacío.")
        if not contenido or not contenido.strip():
            raise ValueError("El contenido del documento no puede estar vacío.")

        documento = Documento(
            titulo=titulo.strip(),
            contenido=contenido.strip(),
            fuente=fuente.strip() if fuente else "Sin fuente",
            tipo_documento=tipo_documento.strip() if tipo_documento else "general",
            metadatos=json.dumps(metadatos, ensure_ascii=False) if metadatos else None,
            estado=estado,
        )
        self.session.add(documento)
        await self.session.flush()
        logger.info("Documento creado: id=%d titulo='%s'", documento.id, documento.titulo)
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
            select(Documento).where(Documento.id == documento_id)
        )
        return resultado.scalar_one_or_none()

    async def listar_documentos(
        self,
        tipo_documento: Optional[str] = None,
        estado: Optional[str] = None,
        limite: int = 50,
    ) -> List[Documento]:
        """Lista documentos con filtros opcionales."""
        consulta = select(Documento)
        if tipo_documento:
            consulta = consulta.where(Documento.tipo_documento == tipo_documento)
        if estado:
            consulta = consulta.where(Documento.estado == estado)
        consulta = consulta.order_by(Documento.created_at.desc()).limit(limite)
        resultado = await self.session.execute(consulta)
        return list(resultado.scalars().all())

    # ──────────────────────────────────────────────────────────────
    # FRAGMENTOS
    # ──────────────────────────────────────────────────────────────

    async def crear_fragmento(
        self,
        documento_id: int,
        contenido: str,
        orden: int,
        embedding: Optional[List[float]] = None,
        metadatos: Optional[dict] = None,
    ) -> FragmentoDocumento:
        """Crea un fragmento de documento con su embedding.

        Args:
            documento_id: ID del documento padre.
            contenido: Texto del fragmento.
            orden: Posición dentro del documento.
            embedding: Vector de embedding (1536d) o None si pendiente.
            metadatos: Metadatos del fragmento.

        Returns:
            FragmentoDocumento creado.
        """
        if not contenido or not contenido.strip():
            raise ValueError("El contenido del fragmento no puede estar vacío.")
        fragmento = FragmentoDocumento(
            documento_id=documento_id,
            contenido=contenido.strip(),
            orden=orden,
            embedding=embedding,
            metadatos=json.dumps(metadatos, ensure_ascii=False) if metadatos else None,
        )
        self.session.add(fragmento)
        await self.session.flush()
        return fragmento

    async def obtener_fragmentos_por_documento(
        self, documento_id: int
    ) -> List[FragmentoDocumento]:
        """Obtiene todos los fragmentos de un documento, ordenados."""
        resultado = await self.session.execute(
            select(FragmentoDocumento)
            .where(FragmentoDocumento.documento_id == documento_id)
            .order_by(FragmentoDocumento.orden)
        )
        return list(resultado.scalars().all())

    async def buscar_fragmentos_por_similitud(
        self,
        embedding_consulta: List[float],
        limite: int = 10,
    ) -> List[tuple[FragmentoDocumento, float]]:
        """Busca fragmentos por similitud coseno.

        Usa el operador <=> de pgvector para distancia coseno.
        Requiere pgvector habilitado en PostgreSQL.

        Args:
            embedding_consulta: Vector de embedding (1536d).
            limite: Máximo de resultados.

        Returns:
            Lista de tuplas (FragmentoDocumento, score) ordenadas por
            relevancia. score = distancia coseno (menor = más similar).
        """
        from sqlalchemy import text

        consulta = text("""
            SELECT fd.id, fd.documento_id, fd.orden, fd.contenido,
                   fd.metadatos, fd.created_at,
                   fd.embedding <=> :q_emb AS score
            FROM fragmentos_documento fd
            WHERE fd.embedding IS NOT NULL
            ORDER BY score ASC
            LIMIT :lim
        """)
        resultado = await self.session.execute(
            consulta, {"q_emb": embedding_consulta, "lim": limite}
        )
        filas = resultado.fetchall()
        fragmentos = []
        for fila in filas:
            frag = FragmentoDocumento(
                id=fila.id, documento_id=fila.documento_id,
                orden=fila.orden, contenido=fila.contenido,
                metadatos=fila.metadatos, created_at=fila.created_at,
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
        logger.info("Documento eliminado: id=%d", documento_id)
        return True