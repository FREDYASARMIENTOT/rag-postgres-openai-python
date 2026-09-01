"""
Configuración compartida de pytest para el RAG Institucional.

Define:
- Marcadores personalizados (unit, integration, azure).
- Fixtures compartidos entre todos los tests.
- Configuración condicional para tests AZURE.
"""

from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# MARCADORES PERSONALIZADOS
# =============================================================================


def pytest_configure(config):
    """Registra marcadores personalizados para clasificación de tests."""
    config.addinivalue_line("markers", "unit: Test de unidad sin dependencias externas.")
    config.addinivalue_line("markers", "integration: Test de integración con componentes mockeados.")
    config.addinivalue_line(
        "markers",
        "azure: Test que requiere Azure o PostgreSQL real. "
        "Usar --run-azure para ejecutar.",
    )


def pytest_addoption(parser):
    """Añade opción --run-azure para ejecutar tests que requieren Azure."""
    parser.addoption(
        "--run-azure",
        action="store_true",
        default=False,
        help="Ejecutar tests que requieren conexión Azure/PostgreSQL real.",
    )


def pytest_collection_modifyitems(config, items):
    """Omite tests marcados como 'azure' a menos que se pase --run-azure."""
    if config.getoption("--run-azure"):
        return  # Ejecutar todos los tests
    skip_azure = pytest.mark.skip(reason="Requiere --run-azure para ejecutar. Saltando test azure.")
    for item in items:
        if "azure" in item.keywords:
            item.add_marker(skip_azure)


# =============================================================================
# FIXTURES COMPARTIDOS
# =============================================================================


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """
    Fixture que retorna un mock del cliente AsyncOpenAI.

    Simula la respuesta del endpoint de embeddings sin llamar a la API real.
    Útil para tests unitarios de búsqueda y generación.

    Returns:
        AsyncMock configurado con un método .embeddings.create que retorna
        un vector de 1024 dimensiones.
    """
    client = AsyncMock(spec=AsyncOpenAI)

    # Mock de embeddings.create
    mock_embedding = AsyncMock()
    mock_embedding.data = [MagicMock(embedding=[0.1] * 1024)]
    client.embeddings.create = AsyncMock(return_value=mock_embedding)

    # Mock de chat.completions.create
    mock_chunk = MagicMock()
    mock_choice = MagicMock()
    mock_delta = MagicMock(content="Respuesta mockeada del RAG.")
    mock_choice.delta = mock_delta
    mock_chunk.choices = [mock_choice]

    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [mock_chunk]
    client.chat.completions.create = AsyncMock(return_value=mock_stream)

    return client


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """
    Fixture que retorna un mock de AsyncSession.

    Simula sesión de base de datos sin conexión real a PostgreSQL.
    """
    session = AsyncMock(spec=AsyncSession)

    # Mock para execute() -> fetchall()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = None
    session.execute = AsyncMock(return_value=mock_result)
    session.scalars = AsyncMock(return_value=mock_result)

    return session


@pytest.fixture
def sample_filters_valid() -> list[dict[str, Any]]:
    """Filtros de ejemplo válidos para tests de seguridad SQL."""
    return [
        {"column": "price", "comparison_operator": ">", "value": 30.0},
        {"column": "brand", "comparison_operator": "=", "value": "AirStrider"},
    ]


@pytest.fixture
def sample_filters_invalid_column() -> list[dict[str, Any]]:
    """Filtros con columna no permitida (debe ser rechazado por whitelist)."""
    return [
        {"column": "embedding_3l", "comparison_operator": "=", "value": 0.5},
    ]


@pytest.fixture
def sample_filters_sql_injection() -> list[dict[str, Any]]:
    """Filtros con intento de inyección SQL en el valor."""
    return [
        {"column": "brand", "comparison_operator": "=", "value": "AirStrider'; DROP TABLE items; --"},
    ]


# =============================================================================
# FIXTURES DE CONFIGURACIÓN
# =============================================================================


class MockArgs:
    """Simula argparse.Namespace para pruebas de create_postgres_engine_from_args."""

    def __init__(self, host="localhost", username="test", database="test_db",
                 password="test_pass", sslmode=None, tenant_id=None):
        self.host = host
        self.username = username
        self.database = database
        self.password = password
        self.sslmode = sslmode
        self.tenant_id = tenant_id


@pytest.fixture
def mock_args_local() -> MockArgs:
    """Argumentos simulados para conexión PostgreSQL local."""
    return MockArgs()


@pytest.fixture
def mock_args_azure() -> MockArgs:
    """Argumentos simulados para conexión Azure Database for PostgreSQL."""
    return MockArgs(host="supersetdev.postgres.database.azure.com")