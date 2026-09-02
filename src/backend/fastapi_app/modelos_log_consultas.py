"""
Modelos del schema log — Consultas detalle y eventos
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
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_app.postgres_models import Base


class ConsultaDocumento(Base):
    __tablename__ = "consultas_documentos"
    __table_args__ = {"schema": "log"}

    id_consulta_documento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_consulta: Mapped[int] = mapped_column(
        Integer, ForeignKey("log.consultas.id_consulta", ondelete="RESTRICT"), nullable=False
    )
    id_documento: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.documentos.id_documento", ondelete="RESTRICT"), nullable=False
    )
    posicion_resultado: Mapped[Optional[int]] = mapped_column(Integer)
    puntaje_similitud: Mapped[Optional[float]] = mapped_column(Numeric(10, 8))
    fue_utilizado_respuesta: Mapped[Optional[bool]] = mapped_column(Boolean)
    fecha_registro: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_registro: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)


class ConsultaFragmento(Base):
    __tablename__ = "consultas_fragmentos"
    __table_args__ = {"schema": "log"}

    id_consulta_fragmento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_consulta: Mapped[int] = mapped_column(
        Integer, ForeignKey("log.consultas.id_consulta", ondelete="RESTRICT"), nullable=False
    )
    id_fragmento: Mapped[int] = mapped_column(
        Integer, ForeignKey("rag.fragmentos_documento.id_fragmento", ondelete="RESTRICT"), nullable=False
    )
    posicion_resultado: Mapped[Optional[int]] = mapped_column(Integer)
    puntaje_similitud: Mapped[Optional[float]] = mapped_column(Numeric(10, 8))
    fue_utilizado_respuesta: Mapped[Optional[bool]] = mapped_column(Boolean)
    fecha_registro: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_registro: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)


class EventoDocumento(Base):
    __tablename__ = "eventos_documentos"
    __table_args__ = {"schema": "log"}

    id_evento: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_documento: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("rag.documentos.id_documento", ondelete="SET NULL"), nullable=True
    )
    tipo_evento: Mapped[str] = mapped_column(String(30), nullable=False)
    descripcion_evento: Mapped[Optional[str]] = mapped_column(Text)
    usuario_evento: Mapped[Optional[str]] = mapped_column(String(200))
    identificador_usuario_evento: Mapped[Optional[str]] = mapped_column(String(200))
    fecha_evento: Mapped[datetime.date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    hora_evento: Mapped[datetime.time] = mapped_column(Time, server_default=func.current_time(), nullable=False)
    datos_evento_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    resultado_evento: Mapped[Optional[str]] = mapped_column(String(30))