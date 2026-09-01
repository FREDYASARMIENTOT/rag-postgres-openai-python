"""
Tests UNIT e INTEGRATION para la capa de embeddings.

Cobertura:
- UNIT 1: Validación de modelos que requieren dimensions.
- UNIT 2: Validación de modelos que NO requieren dimensions.
- UNIT 3: Modelo no soportado (ninguno de los conocidos).
- UNIT 4: Llamada exitosa a compute_text_embedding.
- AZURE 1: Llamada real a Azure OpenAI (solo con --run-azure).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from fastapi_app.embeddings import (
    MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES,
    compute_text_embedding,
)


# =============================================================================
# TESTS UNIT: MODELOS DE EMBEDDING
# =============================================================================


@pytest.mark.unit
class TestModelosEmbeddingConocidos:
    """Verifica el conjunto de modelos conocidos que soportan dimensions."""

    def test_modelos_con_dimensiones(self):
        """Verifica que text-embedding-3-large y 3-small están en el conjunto."""
        assert "text-embedding-3-large" in MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES
        assert "text-embedding-3-small" in MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES

    def test_modelo_sin_dimensiones(self):
        """Verifica que text-embedding-ada-002 NO está en el conjunto."""
        assert "text-embedding-ada-002" not in MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES

    def test_modelo_desconocido(self):
        """Verifica que un modelo desconocido NO está en el conjunto."""
        assert "modelo-inexistente-v1" not in MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES


# =============================================================================
# TESTS UNIT: COMPUTE_TEXT_EMBEDDING
# =============================================================================


@pytest.mark.unit
class TestComputeTextEmbeddingConfig:
    """Prueba la validación de configuración antes de llamar a la API."""

    @pytest.mark.parametrize("modelo", [
        "text-embedding-3-large",
        "text-embedding-3-small",
    ])
    @pytest.mark.asyncio
    async def test_modelo_requiere_dimensions_sin_dimensiones(self, modelo):
        """
        Si el modelo soporta dimensions pero no se proporcionan,
        debe lanzar ValueError.
        """
        cliente_mock = AsyncMock()
        with pytest.raises(ValueError, match="requiere"):
            await compute_text_embedding(
                texto_consulta="test query",
                cliente_openai=cliente_mock,
                modelo_embedding=modelo,
                deployment_embedding=None,
                dimensiones_embedding=None,
            )
        # Verificar que NO se llamó a la API
        cliente_mock.embeddings.create.assert_not_called()

    @pytest.mark.parametrize("modelo", [
        "text-embedding-ada-002",
        "nomic-embed-text",
        "modelo-desconocido-test",
    ])
    @pytest.mark.asyncio
    async def test_modelo_sin_dimensions_con_dimensiones(self, modelo, mock_openai_client):
        """
        Si el modelo NO soporta dimensions pero se proporcionan,
        debe ignorarlas silenciosamente (compatibilidad).
        """
        vector = await compute_text_embedding(
            texto_consulta="test query",
            cliente_openai=mock_openai_client,
            modelo_embedding=modelo,
            deployment_embedding=None,
            dimensiones_embedding=1024,  # Se ignora
        )
        assert len(vector) == 1024
        mock_openai_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_llamada_con_deployment_azure(self, mock_openai_client):
        """
        Verifica que en modo Azure, el nombre del modelo API
        sea el deployment, no el nombre del modelo.
        """
        await compute_text_embedding(
            texto_consulta="test",
            cliente_openai=mock_openai_client,
            modelo_embedding="text-embedding-3-large",
            deployment_embedding="mi-deployment-embedding",
            dimensiones_embedding=1024,
        )
        # El primer argumento posicional de create() es model=...
        call_model = mock_openai_client.embeddings.create.call_args[1].get("model")
        assert call_model == "mi-deployment-embedding", (
            f"Esperaba 'mi-deployment-embedding' pero recibió '{call_model}'"
        )

    @pytest.mark.asyncio
    async def test_llamada_sin_deployment(self, mock_openai_client):
        """
        Verifica que sin deployment, el nombre del modelo API
        sea el nombre del modelo directamente.
        """
        await compute_text_embedding(
            texto_consulta="test",
            cliente_openai=mock_openai_client,
            modelo_embedding="text-embedding-3-large",
            deployment_embedding=None,
            dimensiones_embedding=1024,
        )
        call_model = mock_openai_client.embeddings.create.call_args[1].get("model")
        assert call_model == "text-embedding-3-large"


# =============================================================================
# TESTS AZURE: E2E (requieren --run-azure y credenciales reales)
# =============================================================================


@pytest.mark.azure
@pytest.mark.skip(reason="Requiere despliegue activo de embeddings en Azure.")
class TestComputeTextEmbeddingReal:
    """
    Tests E2E contra Azure OpenAI real.

    Requisitos:
    - --run-azure habilitado.
    - AZURE_OPENAI_ENDPOINT configurado.
    - Deployment 'text-embedding-3-large' existente en Modelo-IA-UR.
    - Variables de entorno configuradas.

    Estado actual (Fase 3):
      No hay deployment de embeddings confirmado en Modelo-IA-UR.
      gpt-4o-mini (sii-supervisor-gpt-4o-mini) está pendiente de
      verificación para soporte de /embeddings.
    """

    @pytest.mark.asyncio
    async def test_embedding_real(self):
        """Este test está pendiente de confirmación del deployment."""
        pytest.skip(
            "No hay deployment de embeddings confirmado todavía. "
            "Verificar si gpt-4o-mini en Modelo-IA-UR soporta /embeddings."
        )