"""
Tests unitarios para el módulo proveedores.py.

Valida:
1. Contratos abstractos ProveedorLLM y ProveedorEmbeddings.
2. Implementaciones concretas ProveedorLLMBase y ProveedorEmbeddingsBase.
3. Factory functions crear_proveedor_llm y crear_proveedor_embeddings.
4. Configuración de modelo, deployment y dimensiones.
5. Que NO hay nombres de modelos hardcodeados en lógica de negocio.

NO llama a Azure. Usa mocks.
"""

from unittest.mock import AsyncMock

import pytest
from openai import AsyncOpenAI

from fastapi_app.proveedores import (
    ProveedorEmbeddings,
    ProveedorEmbeddingsBase,
    ProveedorLLM,
    ProveedorLLMBase,
    crear_proveedor_embeddings,
    crear_proveedor_llm,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_async_openai_client() -> AsyncMock:
    """Cliente AsyncOpenAI mockeado para tests."""
    return AsyncMock(spec=AsyncOpenAI)


# =============================================================================
# TESTS: CONTRATOS ABSTRACTOS
# =============================================================================


class TestProveedorLLMContract:

    def test_no_se_puede_instanciar_directamente(self):
        """ProveedorLLM es abstracto — no se puede instanciar."""
        with pytest.raises(TypeError):
            ProveedorLLM()  # type: ignore


class TestProveedorEmbeddingsContract:

    def test_no_se_puede_instanciar_directamente(self):
        """ProveedorEmbeddings es abstracto — no se puede instanciar."""
        with pytest.raises(TypeError):
            ProveedorEmbeddings()  # type: ignore


# =============================================================================
# TESTS: IMPLEMENTACIÓN ProveedorLLMBase
# =============================================================================


class TestProveedorLLMBase:

    def test_creacion_minima(self, mock_async_openai_client):
        """Crear ProveedorLLMBase solo con cliente y modelo."""
        provider = ProveedorLLMBase(
            cliente=mock_async_openai_client,
            modelo="gpt-5.6-luna",
        )
        assert provider.cliente is mock_async_openai_client
        assert provider.modelo == "gpt-5.6-luna"
        assert provider.deployment is None

    def test_creacion_con_deployment(self, mock_async_openai_client):
        """Crear ProveedorLLMBase con deployment."""
        provider = ProveedorLLMBase(
            cliente=mock_async_openai_client,
            modelo="gpt-5.6-luna",
            deployment="ur-rag-gpt-5-6-luna",
        )
        assert provider.modelo == "gpt-5.6-luna"
        assert provider.deployment == "ur-rag-gpt-5-6-luna"

    def test_cliente_devuelto_correctamente(self, mock_async_openai_client):
        """La propiedad cliente debe devolver la misma instancia."""
        provider = ProveedorLLMBase(cliente=mock_async_openai_client, modelo="gpt-4o-mini")
        assert provider.cliente is mock_async_openai_client


# =============================================================================
# TESTS: IMPLEMENTACIÓN ProveedorEmbeddingsBase
# =============================================================================


class TestProveedorEmbeddingsBase:

    def test_creacion_minima(self, mock_async_openai_client):
        """Crear ProveedorEmbeddingsBase solo con cliente y modelo."""
        provider = ProveedorEmbeddingsBase(
            cliente=mock_async_openai_client,
            modelo="text-embedding-3-large",
        )
        assert provider.cliente is mock_async_openai_client
        assert provider.modelo == "text-embedding-3-large"
        assert provider.deployment is None
        assert provider.dimensiones is None

    def test_creacion_completa(self, mock_async_openai_client):
        """Crear ProveedorEmbeddingsBase con todos los campos."""
        provider = ProveedorEmbeddingsBase(
            cliente=mock_async_openai_client,
            modelo="text-embedding-3-large",
            deployment="ur-rag-embedding-3-large",
            dimensiones=1024,
        )
        assert provider.modelo == "text-embedding-3-large"
        assert provider.deployment == "ur-rag-embedding-3-large"
        assert provider.dimensiones == 1024

    def test_dimensiones_pueden_ser_none(self, mock_async_openai_client):
        """Dimensiones debe poder ser None para modelos que no soportan dimensions."""
        provider = ProveedorEmbeddingsBase(
            cliente=mock_async_openai_client,
            modelo="nomic-embed-text",
            dimensiones=None,
        )
        assert provider.dimensiones is None
# =============================================================================
# TESTS: FACTORY FUNCTIONS
# =============================================================================


class TestCrearProveedorLLM:

    def test_factory_devuelve_proveedor_llm_base(self, mock_async_openai_client):
        """crear_proveedor_llm debe devolver ProveedorLLMBase."""
        provider = crear_proveedor_llm(
            cliente=mock_async_openai_client,
            modelo="gpt-5.6-luna",
        )
        assert isinstance(provider, ProveedorLLM)
        assert isinstance(provider, ProveedorLLMBase)

    def test_factory_con_deployment(self, mock_async_openai_client):
        """Probar factory con deployment."""
        provider = crear_proveedor_llm(
            cliente=mock_async_openai_client,
            modelo="gpt-5.6-luna",
            deployment="ur-rag-gpt-5-6-luna",
        )
        assert provider.deployment == "ur-rag-gpt-5-6-luna"

    def test_factory_sin_deployment(self, mock_async_openai_client):
        """Probar factory sin deployment (modo OpenAI.com)."""
        provider = crear_proveedor_llm(
            cliente=mock_async_openai_client,
            modelo="gpt-5.6-luna",
        )
        assert provider.deployment is None


class TestCrearProveedorEmbeddings:

    def test_factory_devuelve_proveedor_embeddings_base(self, mock_async_openai_client):
        """crear_proveedor_embeddings debe devolver ProveedorEmbeddingsBase."""
        provider = crear_proveedor_embeddings(
            cliente=mock_async_openai_client,
            modelo="text-embedding-3-large",
        )
        assert isinstance(provider, ProveedorEmbeddings)
        assert isinstance(provider, ProveedorEmbeddingsBase)

    def test_factory_con_dimensiones(self, mock_async_openai_client):
        """Probar factory con dimensiones específicas."""
        provider = crear_proveedor_embeddings(
            cliente=mock_async_openai_client,
            modelo="text-embedding-3-large",
            deployment="ur-rag-embedding-3-large",
            dimensiones=1024,
        )
        assert provider.dimensiones == 1024

    def test_factory_sin_dimensiones(self, mock_async_openai_client):
        """Probar factory sin dimensiones."""
        provider = crear_proveedor_embeddings(
            cliente=mock_async_openai_client,
            modelo="nomic-embed-text",
        )
        assert provider.dimensiones is None


# =============================================================================
# TESTS: COMPORTAMIENTO Y NO HARDCODEO
# =============================================================================


class TestNoHardcodeo:

    def test_proveedor_llm_no_hardcodea_modelo(self, mock_async_openai_client):
        """El proveedor acepta cualquier nombre de modelo desde config."""
        modelos = ["gpt-5.6-luna", "gpt-4o-mini", "gpt-4", "phi3:3.8b"]
        for modelo in modelos:
            provider = ProveedorLLMBase(cliente=mock_async_openai_client, modelo=modelo)
            assert provider.modelo == modelo

    def test_proveedor_embeddings_no_hardcodea_modelo(self, mock_async_openai_client):
        """El proveedor de embeddings acepta cualquier modelo desde config."""
        modelos = [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
            "nomic-embed-text",
        ]
        for modelo in modelos:
            provider = ProveedorEmbeddingsBase(cliente=mock_async_openai_client, modelo=modelo)
            assert provider.modelo == modelo

    def test_proveedor_embeddings_no_hardcodea_dimensiones(self, mock_async_openai_client):
        """Las dimensiones vienen de config, no están fijas en código."""
        dimensiones = [None, 256, 512, 768, 1024, 1536, 3072]
        for dim in dimensiones:
            provider = ProveedorEmbeddingsBase(
                cliente=mock_async_openai_client,
                modelo="text-embedding-3-small",
                dimensiones=dim,
            )
            assert provider.dimensiones == dim


# =============================================================================
# TESTS: ERRORES
# =============================================================================


class TestErrores:

    def test_crear_proveedor_sin_cliente_llm(self):
        """Crear ProveedorLLMBase sin cliente debe fallar."""
        with pytest.raises(TypeError):
            ProveedorLLMBase()  # type: ignore

    def test_crear_proveedor_sin_modelo_embeddings(self, mock_async_openai_client):
        """Crear ProveedorEmbeddingsBase sin modelo debe fallar."""
        with pytest.raises(TypeError):
            ProveedorEmbeddingsBase(cliente=mock_async_openai_client)  # type: ignore