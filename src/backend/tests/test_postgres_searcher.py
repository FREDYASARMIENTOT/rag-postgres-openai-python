"""
Tests UNIT e INTEGRATION para PostgresSearcher.

Cobertura de seguridad SQL:
- UNIT 1: Filtros con columnas válidas -> se aplican.
- UNIT 2: Filtros con columnas inválidas -> se omiten.
- UNIT 3: Filtros con operadores inválidos -> se omiten.
- UNIT 4: Inyección SQL en valor de string -> escape de comillas.
- UNIT 5: Filtros mixtos (válidos e inválidos) -> solo válidos pasan.
- UNIT 6: Filtros vacíos/None -> cadenas vacías.

Cobertura de lógica de búsqueda:
- INTEGRATION 1: search_and_embed con vector search.
- INTEGRATION 2: search_and_embed con text search only.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_app.api_models import Filter
from fastapi_app.postgres_searcher import (
    COLUMNAS_FILTRO_PERMITIDAS,
    OPERADORES_FILTRO_PERMITIDOS,
    PostgresSearcher,
)


# =============================================================================
# Fixtures específicos para este módulo
# =============================================================================


@pytest.fixture
def searcher(mock_db_session: AsyncMock, mock_openai_client) -> PostgresSearcher:
    """Crea un PostgresSearcher con dependencias mockeadas."""
    return PostgresSearcher(
        db_session=mock_db_session,
        openai_embed_client=mock_openai_client,
        embed_deployment="text-embedding-3-large",
        embed_model="text-embedding-3-large",
        embed_dimensions=1024,
        embedding_column="embedding_3l",
    )


# =============================================================================
# TESTS UNIT: LISTAS BLANCAS
# =============================================================================


@pytest.mark.unit
class TestWhitelists:
    """Verifica la composición de las listas blancas de seguridad."""

    def test_columnas_permitidas(self):
        """Verifica columnas conocidas en la whitelist."""
        assert "price" in COLUMNAS_FILTRO_PERMITIDAS
        assert "brand" in COLUMNAS_FILTRO_PERMITIDAS
        assert "type" in COLUMNAS_FILTRO_PERMITIDAS
        assert "name" in COLUMNAS_FILTRO_PERMITIDAS

    def test_columnas_no_permitidas(self):
        """Verifica que columnas sensibles NO estén en la whitelist."""
        assert "id" not in COLUMNAS_FILTRO_PERMITIDAS
        assert "embedding_3l" not in COLUMNAS_FILTRO_PERMITIDAS
        assert "embedding_nomic" not in COLUMNAS_FILTRO_PERMITIDAS
        assert "description" not in COLUMNAS_FILTRO_PERMITIDAS

    def test_operadores_peligrosos_no_permitidos(self):
        """Verifica que operadores SQL peligrosos NO estén permitidos."""
        assert "LIKE" not in OPERADORES_FILTRO_PERMITIDOS
        assert "IN" not in OPERADORES_FILTRO_PERMITIDOS
        assert "BETWEEN" not in OPERADORES_FILTRO_PERMITIDOS
        assert "IS" not in OPERADORES_FILTRO_PERMITIDOS
        assert "NOT" not in OPERADORES_FILTRO_PERMITIDOS
        assert "ILIKE" not in OPERADORES_FILTRO_PERMITIDOS
        assert "--" not in OPERADORES_FILTRO_PERMITIDOS


# =============================================================================
# TESTS UNIT: BUILD_FILTER_CLAUSE
# =============================================================================


@pytest.mark.unit
class TestBuildFilterClause:
    """Prueba la construcción segura de cláusulas WHERE/AND."""

    def test_filtros_vacios(self, searcher):
        """Filtros None y lista vacía deben retornar strings vacías."""
        assert searcher.build_filter_clause(None) == ("", "")
        assert searcher.build_filter_clause([]) == ("", "")

    def test_filtros_validos(self, searcher, sample_filters_valid):
        """Filtros con columnas y operadores válidos deben aplicarse."""
        filtros = [Filter(**f) for f in sample_filters_valid]
        where_clause, and_clause = searcher.build_filter_clause(filtros)
        assert "price > 30.0" in where_clause
        assert "brand = 'AirStrider'" in where_clause
        assert where_clause.startswith("WHERE ")
        assert and_clause.startswith("AND ")

    def test_columna_invalida(self, searcher, sample_filters_invalid_column):
        """Filtros con columna no autorizada deben omitirse silenciosamente."""
        filtros = [Filter(**f) for f in sample_filters_invalid_column]
        where_clause, and_clause = searcher.build_filter_clause(filtros)
        assert where_clause == ""
        assert and_clause == ""

    def test_inyeccion_sql(self, searcher, sample_filters_sql_injection):
        """Intento de inyección SQL: comillas simples deben escaparse."""
        filtros = [Filter(**f) for f in sample_filters_sql_injection]
        where_clause, _ = searcher.build_filter_clause(filtros)
        assert "''" in where_clause, f"Comillas sin escapar. Cláusula: {where_clause}"

    def test_filtros_mixtos(self, searcher, sample_filters_valid, sample_filters_invalid_column):
        """Filtros válidos e inválidos mezclados: solo válidos aparecen."""
        filtros = [Filter(**f) for f in sample_filters_valid + sample_filters_invalid_column]
        where_clause, _ = searcher.build_filter_clause(filtros)
        assert "price > 30.0" in where_clause
        assert "embedding_3l" not in where_clause

    def test_operador_invalido(self, searcher):
        """Operador LIKE (no permitido) debe ser omitido."""
        filtros = [Filter(column="brand", comparison_operator="LIKE", value="%Air%")]
        where_clause, _ = searcher.build_filter_clause(filtros)
        assert where_clause == ""


# =============================================================================
# TESTS UNIT: SEARCH_AND_EMBED
# =============================================================================


@pytest.mark.unit
class TestSearchAndEmbed:
    """Prueba la orquestación de search_and_embed."""

    @pytest.mark.asyncio
    async def test_vector_search_sin_texto(self, searcher):
        """enable_vector_search=True pero query_text=None: no genera embedding."""
        with patch.object(searcher, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            resultado = await searcher.search_and_embed(
                query_text=None, top=5,
                enable_vector_search=True, enable_text_search=False,
            )
            mock_search.assert_awaited_once()
            assert resultado == []

    @pytest.mark.asyncio
    async def test_text_search_sin_vector(self, searcher):
        """Solo búsqueda textual, sin vector."""
        with patch.object(searcher, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            resultado = await searcher.search_and_embed(
                query_text="test query", top=5,
                enable_vector_search=False, enable_text_search=True,
            )
            mock_search.assert_awaited_once()
            args, _ = mock_search.call_args
            assert args[0] == "test query"
            assert args[1] == []


# =============================================================================
# TESTS AZURE (requieren --run-azure)
# =============================================================================


@pytest.mark.azure
class TestPostgresSearcherReal:
    """Tests E2E contra PostgreSQL real (pendiente Fase 4)."""

    @pytest.mark.asyncio
    async def test_conexion_real(self):
        pytest.skip(
            "Requiere pgvector habilitado y BD rag_institucional. "
            "Pendiente de aprobación Fase 4."
        )