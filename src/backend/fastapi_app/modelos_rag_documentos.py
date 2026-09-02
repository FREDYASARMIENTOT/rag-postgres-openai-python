"""
Modelos del schema rag — Documentos, fragmentos y clasificacion
FASE F: Universidad del Rosario
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from fastapi_app.modelos_rag_catalogo import FormatoArchivo, Periodo, SerieDocumental
    from fastapi_app.modelos_rag_clasificacion import DocumentoTema, FragmentoDocumento

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import SmallInteger

from fastapi_app.postgres_models import Base


class Documento(Base):
    __tablename__ = "documentos"
    __table_args__ = (
        CheckConstraint("version_documento >= 1", name="ck_version_documento"),
        CheckConstraint("cantidad_consultas >= 0", name="ck_cantidad_consultas"),
        CheckConstraint(
            "estado_vigencia IN ('VIGENTE','HISTORICO','REEMPLAZADO','ARCHIVADO','RETIRADO')",
            name="ck_estado_vigencia",
        ),
        {"schema": "rag"},
    )

    id_documento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_serie_documental: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.series_documentales.id_serie_documental", ondelete="RESTRICT"), nullable=False
    )
    id_periodo: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("rag.periodos.id_periodo", ondelete="SET NULL"), nullable=True
    )
    # === FASE F.2: Formato de archivo ===
    id_formato_archivo: Mapped[Optional[int]] = mapped_column(
        SmallInteger, ForeignKey("rag.formatos_archivo.id_formato_archivo", ondelete="SET NULL"), nullable=True
    )
    titulo_documento: Mapped[str] = mapped_column(String(500), nullable=False)
    descripcion_documento: Mapped[Optional[str]] = mapped_column(Text)
    tipo_documento: Mapped[Optional[str]] = mapped_column(String(100))
    # === FASE F.2: Metadatos de archivo ===
    nombre_archivo_original: Mapped[Optional[str]] = mapped_column(String(500))
    extension_archivo: Mapped[Optional[str]] = mapped_column(String(20))
    mime_type: Mapped[Optional[str]] = mapped_column(String(150))
    cantidad_paginas: Mapped[Optional[int]] = mapped_column(SmallInteger)
    ruta_origen: Mapped[Optional[str]] = mapped_column(Text)
    fuente_documento: Mapped[Optional[str]] = mapped_column(String(300))
    usuario_cargador: Mapped[Optional[str]] = mapped_column(String(200))
    identificador_usuario_cargador: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_documento: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_documento: Mapped[Optional[datetime.time]] = mapped_column(Time)
    fecha_corte: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_corte: Mapped[Optional[datetime.time]] = mapped_column(Time)
    fecha_carga: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_carga: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    tamano_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    hash_sha256: Mapped[Optional[str]] = mapped_column(String(64))
    version_documento: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    id_documento_anterior: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("rag.documentos.id_documento", ondelete="SET NULL"), nullable=True
    )
    estado_vigencia: Mapped[str] = mapped_column(String(30), default="VIGENTE", nullable=False)
    es_documento_critico: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    participa_retrieval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cantidad_consultas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fecha_ultima_consulta: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_ultima_consulta: Mapped[Optional[datetime.time]] = mapped_column(Time)
    fecha_archivado: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_archivado: Mapped[Optional[datetime.time]] = mapped_column(Time)
    fecha_creacion: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_creacion: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    fecha_actualizacion: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_actualizacion: Mapped[Optional[datetime.time]] = mapped_column(Time)

    # Relationships using string references
    serie_documental: Mapped["SerieDocumental"] = relationship(
        "SerieDocumental", back_populates="documentos"
    )
    periodo: Mapped[Optional["Periodo"]] = relationship("Periodo")
    formato_archivo: Mapped[Optional["FormatoArchivo"]] = relationship("FormatoArchivo", back_populates="documentos")
    documento_anterior: Mapped[Optional["Documento"]] = relationship(
        "Documento", remote_side="Documento.id_documento"
    )
    fragmentos: Mapped[list["FragmentoDocumento"]] = relationship(
        "FragmentoDocumento", back_populates="documento"
    )
    documentos_temas: Mapped[list["DocumentoTema"]] = relationship(
        "DocumentoTema", back_populates="documento"
    )