"""
Modelos del schema rag — Catalogos (series, temas, periodos)
FASE F: Universidad del Rosario
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from fastapi_app.modelos_rag_clasificacion import DocumentoTema
    from fastapi_app.modelos_rag_documentos import Documento

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

from fastapi_app.postgres_models import Base


class SerieDocumental(Base):
    __tablename__ = "series_documentales"
    __table_args__ = {"schema": "rag"}

    id_serie_documental: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_serie: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_serie: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion_serie: Mapped[Optional[str]] = mapped_column(Text)
    periodicidad: Mapped[Optional[str]] = mapped_column(String(30))
    es_serie_critica: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permite_versionamiento: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_creacion: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    fecha_actualizacion: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_actualizacion: Mapped[Optional[datetime.time]] = mapped_column(Time)

    documentos: Mapped[list["Documento"]] = relationship("Documento", back_populates="serie_documental")


class Tema(Base):
    __tablename__ = "temas"
    __table_args__ = (
        CheckConstraint("nivel_jerarquia >= 1", name="ck_nivel_jerarquia"),
        {"schema": "rag"},
    )

    id_tema: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_tema: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_tema: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion_tema: Mapped[Optional[str]] = mapped_column(Text)
    id_tema_padre: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("rag.temas.id_tema", ondelete="RESTRICT"), nullable=True
    )
    nivel_jerarquia: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_creacion: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    fecha_actualizacion: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_actualizacion: Mapped[Optional[datetime.time]] = mapped_column(Time)

    tema_padre: Mapped[Optional["Tema"]] = relationship("Tema", remote_side="Tema.id_tema", backref="subtemas")
    documentos_temas: Mapped[list["DocumentoTema"]] = relationship("DocumentoTema", back_populates="tema")


class Periodo(Base):
    __tablename__ = "periodos"
    __table_args__ = (
        CheckConstraint(
            "tipo_periodo IN ('PUNTUAL','MENSUAL','TRIMESTRAL','SEMESTRAL','ANUAL','BIENAL','PERMANENTE')",
            name="ck_tipo_periodo",
        ),
        {"schema": "rag"},
    )

    id_periodo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_periodo: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo_periodo: Mapped[str] = mapped_column(String(30), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_periodo: Mapped[Optional[int]] = mapped_column(Integer)
    fecha_inicio: Mapped[Optional[datetime.date]] = mapped_column(Date)
    fecha_fin: Mapped[Optional[datetime.date]] = mapped_column(Date)
    descripcion_periodo: Mapped[Optional[str]] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
class FormatoArchivo(Base):
    """Catálogo de formatos de archivo soportados por el RAG Institucional.

    Cada fila representa un formato técnico (PDF, MD, TXT, etc.) con su
    extensión y MIME type. NO confundir con tipo_documento (FACULTADES, REGLAMENTO).
    """

    __tablename__ = "formatos_archivo"
    __table_args__ = {"schema": "rag"}

    id_formato_archivo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_formato: Mapped[str] = mapped_column(String(20), nullable=False)
    extension_archivo: Mapped[str] = mapped_column(String(10), nullable=False)
    tipo_mime: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre_formato: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion_formato: Mapped[Optional[str]] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admite_ingesta: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_creacion: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_creacion: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)

    documentos: Mapped[list["Documento"]] = relationship("Documento", back_populates="formato_archivo")