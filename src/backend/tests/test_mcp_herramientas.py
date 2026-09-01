"""
Tests para herramientas MCP del RAG Institucional.

Valida:
    1. Creación del servidor MCP.
    2. Validación de tipo_documento y límites.
    3. Contratos de herramientas.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from fastapi_app.mcp_servidor import (
    crear_mcp_servidor, _validar_tipo_documento, _validar_limite,
    TIPO_DOCUMENTO_PERMITIDOS, LIMITE_MAXIMO_RESULTADOS,
)
from fastapi_app.repositorio_documentos import RepositorioDocumentos
from fastapi_app.servicio_ingesta import ServicioIngesta, ResultadoIngesta
from fastapi_app.servicio_retrieval import ServicioRetrieval, ResultadoBusqueda


@pytest.fixture
def mock_repo():
    return AsyncMock(spec=RepositorioDocumentos)


@pytest.fixture
def mock_ingesta():
    m = AsyncMock(spec=ServicioIngesta)
    m.ingestar.return_value = ResultadoIngesta(
        documento_id=1, titulo="Test", cantidad_fragmentos=3,
        estado="exitoso", fuente="https://test.urosario.edu.co",
    )
    return m


@pytest.fixture
def mock_retrieval():
    m = AsyncMock(spec=ServicioRetrieval)
    m.consultar.return_value = [
        ResultadoBusqueda(contenido="Facultad de Medicina", documento_id=1,
                          titulo="Facultades UR", fuente="https://test.urosario.edu.co", score=0.15),
    ]
    m.obtener_documento_completo.return_value = {
        "documento_id": 1, "titulo": "Facultades UR", "contenido": "...",
        "fuente": "https://test.urosario.edu.co", "tipo_documento": "facultad",
        "estado": "activo", "metadata": None, "cantidad_fragmentos": 1, "fragmentos": [],
    }
    return m


@pytest.fixture
def servo(mock_repo, mock_ingesta, mock_retrieval):
    return crear_mcp_servidor(repositorio=mock_repo, servicio_ingesta=mock_ingesta,
                              servicio_retrieval=mock_retrieval)


class TestCreacionServidor:
    def test_creacion(self, servo):
        assert servo is not None

    def test_nombre_personalizado(self, mock_repo, mock_ingesta, mock_retrieval):
        s = crear_mcp_servidor(repositorio=mock_repo, servicio_ingesta=mock_ingesta,
                                servicio_retrieval=mock_retrieval, nombre="Test-Server")
        assert s is not None


class TestValidacionTipoDocumento:
    def test_facultad_valido(self):
        assert _validar_tipo_documento("facultad") == "facultad"

    def test_desconocido_vuelve_general(self):
        assert _validar_tipo_documento("hacker") == "general"

    def test_vacio_vuelve_general(self):
        assert _validar_tipo_documento("") == "general"

    def test_mayusculas_normalizadas(self):
        assert _validar_tipo_documento("FACULTAD") == "facultad"

    def test_general_es_valido(self):
        assert _validar_tipo_documento("general") == "general"

    def test_tipos_permitidos_no_vacio(self):
        assert len(TIPO_DOCUMENTO_PERMITIDOS) > 0

    def test_reglamento_en_permitidos(self):
        assert "reglamento" in TIPO_DOCUMENTO_PERMITIDOS


class TestValidacionLimite:
    def test_limite_normal(self):
        assert _validar_limite(5) == 5

    def test_limite_cero(self):
        assert _validar_limite(0) == 1

    def test_limite_negativo(self):
        assert _validar_limite(-3) == 1

    def test_limite_excesivo(self):
        assert _validar_limite(999) == LIMITE_MAXIMO_RESULTADOS

    def test_limite_string(self):
        assert _validar_limite("10") == 10

    def test_limite_invalido(self):
        assert _validar_limite("xyz") == 10
        assert _validar_limite(None) == 10