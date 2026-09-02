"""
Modelos del schema log — Trazabilidad operacional y auditoria
FASE F: Universidad del Rosario
"""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_app.postgres_models import Base


class CargaDocumento(Base):
    __tablename__ = "cargas_documentos"
    __table_args__ = {"schema": "log"}

    id_carga: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_documento: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.documentos.id_documento", ondelete="RESTRICT"), nullable=False
    )
    nombre_archivo: Mapped[Optional[str]] = mapped_column(String(500))
    hash_sha256: Mapped[Optional[str]] = mapped_column(String(64))
    tamano_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    usuario_cargador: Mapped[Optional[str]] = mapped_column(String(200))
    identificador_usuario_cargador: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_carga: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_carga: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    cantidad_fragmentos: Mapped[Optional[int]] = mapped_column(Integer)
    cantidad_embeddings: Mapped[Optional[int]] = mapped_column(Integer)
    estado_carga: Mapped[str] = mapped_column(String(30), default="INICIADA", nullable=False)
    mensaje_resultado: Mapped[Optional[str]] = mapped_column(Text)
    duracion_milisegundos: Mapped[Optional[int]] = mapped_column(Integer)
    fecha_finalizacion: Mapped[Optional[datetime.date]] = mapped_column(Date)
    hora_finalizacion: Mapped[Optional[datetime.time]] = mapped_column(Time)


class Consulta(Base):
    __tablename__ = "consultas"
    __table_args__ = {"schema": "log"}

    id_consulta: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identificador_usuario: Mapped[Optional[str]] = mapped_column(String(200))
    usuario_consulta: Mapped[Optional[str]] = mapped_column(String(200))
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    hash_pregunta: Mapped[Optional[str]] = mapped_column(String(64))
    modo_consulta: Mapped[str] = mapped_column(String(30), default="ACTUAL", nullable=False)
    cantidad_resultados: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    modelo_embedding: Mapped[Optional[str]] = mapped_column(String(100))
    modelo_llm: Mapped[Optional[str]] = mapped_column(String(100))
    deployment_llm: Mapped[Optional[str]] = mapped_column(String(200))
    respuesta_generada: Mapped[Optional[str]] = mapped_column(Text)
    grounding_validado: Mapped[Optional[bool]] = mapped_column(Boolean)
    fecha_consulta: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_consulta: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    duracion_milisegundos: Mapped[Optional[int]] = mapped_column(Integer)
    estado_consulta: Mapped[str] = mapped_column(String(30), default="EXITOSA", nullable=False)
    mensaje_error: Mapped[Optional[str]] = mapped_column(Text)