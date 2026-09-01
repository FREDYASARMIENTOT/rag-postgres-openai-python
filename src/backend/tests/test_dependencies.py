"""
Tests UNIT para las dependencias de FastAPI (dependencies.py).

Cobertura:
- UNIT 1: OpenAIClient model creation.
- UNIT 2: FastAPIAppContext model validation.
"""

import pytest
from pydantic import ValidationError

from fastapi_app.dependencies import FastAPIAppContext, OpenAIClient


@pytest.mark.unit
class TestOpenAIClient:
    """Prueba el contenedor tipado OpenAIClient."""

    def test_creacion_valida(self, mock_openai_client):
        """Verifica que se puede crear con un cliente OpenAI válido."""
        wrapper = OpenAIClient(client=mock_openai_client)
        assert wrapper.client is mock_openai_client

    def test_creacion_sin_cliente(self):
        """Verifica que falla sin el campo 'client'."""
        with pytest.raises(ValidationError):
            OpenAIClient()


@pytest.mark.unit
class TestFastAPIAppContext:
    """Prueba el modelo de contexto compartido."""

    def test_creacion_valida(self):
        """Verifica creación con todos los campos."""
        ctx = FastAPIAppContext(
            openai_chat_model="gpt-4o-mini",
            openai_embed_model="text-embedding-3-large",
            openai_embed_dimensions=1024,
            openai_chat_deployment="sii-supervisor-gpt-4o-mini",
            openai_embed_deployment=None,
            embedding_column="embedding_3l",
        )
        assert ctx.openai_chat_model == "gpt-4o-mini"
        assert ctx.embedding_column == "embedding_3l"
        assert ctx.openai_embed_dimensions == 1024

    def test_campos_opcionales_none(self):
        """Verifica que deployments opcionales puedan ser None."""
        ctx = FastAPIAppContext(
            openai_chat_model="gpt-4o-mini",
            openai_embed_model="text-embedding-3-large",
            openai_embed_dimensions=None,
            openai_chat_deployment=None,
            openai_embed_deployment=None,
            embedding_column="embedding_nomic",
        )
        assert ctx.openai_embed_dimensions is None
        assert ctx.openai_chat_deployment is None
        assert ctx.embedding_column == "embedding_nomic"