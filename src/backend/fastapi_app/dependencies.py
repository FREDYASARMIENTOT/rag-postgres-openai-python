import logging
import os
from collections.abc import AsyncGenerator
from typing import Annotated, Optional

import azure.identity.aio
from fastapi import Depends, Request
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

logger = logging.getLogger("ragapp")


class OpenAIClient(BaseModel):
    """Contenedor tipado para un cliente OpenAI.

    Se usa como dependencia de FastAPI para inyectar el cliente
    de chat o de embeddings en los endpoints.

    Raises en construcción:
        Ninguno. El cliente se entrega ya sea configurado o no;
        la validación ocurre al primer uso (lazy validation).
    """
    client: AsyncOpenAI
    model_config = {"arbitrary_types_allowed": True}


class FastAPIAppContext(BaseModel):
    """Contexto compartido de la aplicación FastAPI.

    Este modelo se construye una vez por request y contiene toda la
    configuración que necesitan los servicios RAG: modelo de chat,
    modelo de embeddings, deployments, y columna de embedding activa.

    Incluye configuración para ambos RAG:
    - RAG Productos (prefijo AZURE_OPENAI_*, OPENAI_*)
    - RAG Institucional (prefijo RAG_*)

    Tipos de campos (RAG Productos):
        openai_chat_host: Host backend para chat (azure, foundry, openai, ollama).
        openai_embed_host: Host backend para embeddings.
        openai_chat_model: Nombre del modelo para chat.
        openai_embed_model: Nombre del modelo para embeddings.
        openai_embed_dimensions: Dimensiones del vector de embedding
                                (None si el modelo no soporta dimensions).
        openai_chat_deployment: Deployment Azure/Foundry (None si no aplica).
        openai_embed_deployment: Deployment Azure/Foundry (None si no aplica).
        foundry_openai_endpoint: Endpoint Foundry (None si no aplica).
        foundry_chat_deployment: Deployment Foundry para chat (None si no aplica).
        foundry_embedding_deployment: Deployment Foundry para embeddings (None si no aplica).
        foundry_embedding_dimensions: Dimensiones Foundry (None si no aplica).
        embedding_column: Nombre de la columna vectorial (embedding_3l o embedding_nomic).

    Tipos de campos (RAG Institucional):
        rag_chat_host: Host backend para chat institucional.
        rag_embed_host: Host backend para embeddings institucional.
        rag_llm_model: Modelo LLM institucional.
        rag_llm_deployment: Deployment LLM institucional.
        rag_embed_model: Modelo de embeddings institucional.
        rag_embed_deployment: Deployment de embeddings institucional.
        rag_embed_dimensions: Dimensiones del embedding institucional.
    """
    # ── RAG Productos ──
    openai_chat_host: str = "azure"
    openai_embed_host: str = "azure"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-large"
    openai_embed_dimensions: Optional[int] = 1024
    openai_chat_deployment: Optional[str] = None
    openai_embed_deployment: Optional[str] = None
    foundry_openai_endpoint: Optional[str] = None
    foundry_chat_deployment: Optional[str] = None
    foundry_embedding_deployment: Optional[str] = None
    foundry_embedding_dimensions: Optional[int] = None
    embedding_column: str = "embedding_3l"

    # ── RAG Institucional ──
    rag_chat_host: str = "foundry"
    """Host backend para chat institucional (foundry, azure, openai, ollama)."""
    rag_embed_host: str = "foundry"
    """Host backend para embeddings institucional."""
    rag_llm_model: str = "gpt-5.6-luna"
    """Modelo LLM institucional."""
    rag_llm_deployment: Optional[str] = "ur-rag-gpt-5-6-luna"
    """Deployment LLM en Azure/Foundry."""
    rag_embed_model: str = "text-embedding-3-small"
    """Modelo de embeddings institucional."""
    rag_embed_deployment: Optional[str] = "ur-rag-embedding-3-small"
    """Deployment de embeddings en Azure/Foundry."""
    rag_embed_dimensions: int = 1536
    """Dimensiones del embedding institucional (text-embedding-3-small = 1536)."""


async def common_parameters():
    """
    Lee y estructura la configuración desde variables de entorno.

    Usa el patrón: `os.getenv("VAR_NAME") or "default_value"`
    para evitar valores vacíos (cadenas vacías).

    Configuración por proveedor de embeddings:

    **Azure OpenAI** (OPENAI_EMBED_HOST == "azure"):
        - AZURE_OPENAI_EMBED_DEPLOYMENT -> deployment (default: text-embedding-3-large)
        - AZURE_OPENAI_EMBED_MODEL -> modelo (default: text-embedding-3-large)
        - AZURE_OPENAI_EMBED_DIMENSIONS -> dimensiones (default: 1024)
        - AZURE_OPENAI_EMBEDDING_COLUMN -> columna vectorial (default: embedding_3l)

    **Foundry** (OPENAI_EMBED_HOST == "foundry"):
        - FOUNDRY_OPENAI_ENDPOINT -> endpoint Foundry
        - FOUNDRY_EMBEDDING_DEPLOYMENT -> deployment (default: text-embedding-3-large)
        - FOUNDRY_EMBEDDING_MODEL -> modelo (default: text-embedding-3-large)
        - FOUNDRY_EMBEDDING_DIMENSIONS -> dimensiones (default: 1024)
        - AZURE_OPENAI_EMBEDDING_COLUMN -> columna vectorial (default: embedding_3l)

    **Ollama** (OPENAI_EMBED_HOST == "ollama"):
        - OLLAMA_EMBED_MODEL -> modelo (default: nomic-embed-text)
        - OLLAMA_EMBEDDING_COLUMN -> columna vectorial (default: embedding_nomic)

    **OpenAI.com** (por defecto):
        - OPENAICOM_EMBED_MODEL -> modelo (default: text-embedding-3-large)
        - OPENAICOM_EMBED_DIMENSIONS -> dimensiones (default: 1024)
        - OPENAICOM_EMBEDDING_COLUMN -> columna vectorial (default: embedding_3l)

    Returns:
        FastAPIAppContext con toda la configuración parseada.

    Nota:
        Esta función NO verifica que los deployments existan realmente.
        Esa validación ocurre al primer intento de uso de la API.
    """
    OPENAI_EMBED_HOST = os.getenv("OPENAI_EMBED_HOST")
    OPENAI_CHAT_HOST = os.getenv("OPENAI_CHAT_HOST")
    # Inicializar campos Foundry como None por defecto
    foundry_openai_endpoint: Optional[str] = None
    foundry_chat_deployment: Optional[str] = None
    foundry_embedding_deployment: Optional[str] = None
    foundry_embedding_dimensions: Optional[int] = None
    if OPENAI_EMBED_HOST == "azure":
        openai_embed_deployment = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT") or "text-embedding-3-large"
        openai_embed_model = os.getenv("AZURE_OPENAI_EMBED_MODEL") or "text-embedding-3-large"
        openai_embed_dimensions = int(os.getenv("AZURE_OPENAI_EMBED_DIMENSIONS") or 1024)
        embedding_column = os.getenv("AZURE_OPENAI_EMBEDDING_COLUMN") or "embedding_3l"
    elif OPENAI_EMBED_HOST == "foundry":
        foundry_openai_endpoint = os.getenv("FOUNDRY_OPENAI_ENDPOINT")
        foundry_embedding_deployment = os.getenv("FOUNDRY_EMBEDDING_DEPLOYMENT") or "ur-rag-embedding-3-large"
        foundry_embedding_dimensions = int(os.getenv("FOUNDRY_EMBEDDING_DIMENSIONS") or 1024)
        openai_embed_deployment = foundry_embedding_deployment
        openai_embed_model = os.getenv("FOUNDRY_EMBEDDING_MODEL") or "text-embedding-3-large"
        openai_embed_dimensions = foundry_embedding_dimensions
        embedding_column = os.getenv("AZURE_OPENAI_EMBEDDING_COLUMN") or "embedding_3l"
    elif OPENAI_EMBED_HOST == "ollama":
        openai_embed_deployment = None
        openai_embed_model = os.getenv("OLLAMA_EMBED_MODEL") or "nomic-embed-text"
        openai_embed_dimensions = None
        embedding_column = os.getenv("OLLAMA_EMBEDDING_COLUMN") or "embedding_nomic"
    else:
        openai_embed_deployment = None
        openai_embed_model = os.getenv("OPENAICOM_EMBED_MODEL") or "text-embedding-3-large"
        openai_embed_dimensions = int(os.getenv("OPENAICOM_EMBED_DIMENSIONS", 1024))
        embedding_column = os.getenv("OPENAICOM_EMBEDDING_COLUMN") or "embedding_3l"
    if OPENAI_CHAT_HOST == "azure":
        openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT") or "gpt-5.4"
        openai_chat_model = os.getenv("AZURE_OPENAI_CHAT_MODEL") or "gpt-5.4"
    elif OPENAI_CHAT_HOST == "foundry":
        foundry_chat_deployment = os.getenv("FOUNDRY_CHAT_DEPLOYMENT") or "ur-rag-gpt-5-6-luna"
        openai_chat_deployment = foundry_chat_deployment
        openai_chat_model = os.getenv("FOUNDRY_CHAT_MODEL") or "gpt-5.6-luna"
    elif OPENAI_CHAT_HOST == "ollama":
        openai_chat_deployment = None
        openai_chat_model = os.getenv("OLLAMA_CHAT_MODEL") or "phi3:3.8b"
        openai_embed_model = os.getenv("OLLAMA_EMBED_MODEL") or "nomic-embed-text"
    else:
        openai_chat_deployment = None
        openai_chat_model = os.getenv("OPENAICOM_CHAT_MODEL") or "gpt-3.5-turbo"
    # ── RAG Institucional ──
    rag_embed_host = os.getenv("RAG_EMBED_HOST", "foundry")
    rag_chat_host = os.getenv("RAG_CHAT_HOST", "foundry")
    rag_llm_model = os.getenv("RAG_LLM_MODEL", "gpt-5.6-luna")
    rag_llm_deployment = os.getenv("RAG_LLM_DEPLOYMENT") or "ur-rag-gpt-5-6-luna"
    rag_embed_model = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small")
    rag_embed_deployment = os.getenv("RAG_EMBEDDING_DEPLOYMENT") or "ur-rag-embedding-3-small"
    try:
        rag_embed_dimensions = int(os.getenv("RAG_EMBEDDING_DIMENSIONS", "1536"))
    except (TypeError, ValueError):
        rag_embed_dimensions = 1536

    return FastAPIAppContext(
        openai_chat_host=OPENAI_CHAT_HOST or "",
        openai_embed_host=OPENAI_EMBED_HOST or "",
        openai_chat_model=openai_chat_model,
        openai_embed_model=openai_embed_model,
        openai_embed_dimensions=openai_embed_dimensions,
        openai_chat_deployment=openai_chat_deployment,
        openai_embed_deployment=openai_embed_deployment,
        foundry_openai_endpoint=foundry_openai_endpoint,
        foundry_chat_deployment=foundry_chat_deployment,
        foundry_embedding_deployment=foundry_embedding_deployment,
        foundry_embedding_dimensions=foundry_embedding_dimensions,
        embedding_column=embedding_column,
        rag_chat_host=rag_chat_host,
        rag_embed_host=rag_embed_host,
        rag_llm_model=rag_llm_model,
        rag_llm_deployment=rag_llm_deployment,
        rag_embed_model=rag_embed_model,
        rag_embed_deployment=rag_embed_deployment,
        rag_embed_dimensions=rag_embed_dimensions,
    )


async def get_azure_credential() -> (
    azure.identity.aio.AzureDeveloperCliCredential | azure.identity.aio.ManagedIdentityCredential
):
    """
    Obtiene una credencial de Azure AD para autenticación.

    Orden de preferencia:
    1. **Managed Identity** (usuario asignado): si APP_IDENTITY_ID está configurado.
    2. **Azure Developer CLI**: si AZURE_TENANT_ID está configurado, usa ese tenant.
    3. **Azure Developer CLI** sin tenant específico.

    Returns:
        Credencial Azure AD lista para usar (AzureDeveloperCliCredential o ManagedIdentityCredential).

    Raises:
        Exception: Si no se puede obtener la credencial (error de autenticación).
    """
    azure_credential: azure.identity.aio.AzureDeveloperCliCredential | azure.identity.aio.ManagedIdentityCredential
    try:
        if client_id := os.getenv("APP_IDENTITY_ID"):
            # Authenticate using a user-assigned managed identity on Azure
            # See web.bicep for value of APP_IDENTITY_ID
            logger.info(
                "Using managed identity for client ID %s",
                client_id,
            )
            azure_credential = azure.identity.aio.ManagedIdentityCredential(client_id=client_id)
        else:
            if tenant_id := os.getenv("AZURE_TENANT_ID"):
                logger.info("Authenticating to Azure using Azure Developer CLI Credential for tenant %s", tenant_id)
                azure_credential = azure.identity.aio.AzureDeveloperCliCredential(tenant_id=tenant_id)
            else:
                logger.info("Authenticating to Azure using Azure Developer CLI Credential")
                azure_credential = azure.identity.aio.AzureDeveloperCliCredential()
        return azure_credential
    except Exception as e:
        logger.warning("Failed to authenticate to Azure: %s", e)
        raise e


async def create_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Crea un sessionmaker asíncrono para SQLAlchemy.

    Args:
        engine: AsyncEngine de SQLAlchemy ya configurado.

    Returns:
        async_sessionmaker con expire_on_commit=False y autoflush=False.

    Nota:
        expire_on_commit=False evita que SQLAlchemy invalide los objetos
        después del commit, permitiendo acceder a atributos fuera de la sesión.
        autoflush=False evita flushes automáticos inesperados.
    """
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_async_sessionmaker(
    request: Request,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    yield request.state.sessionmaker


async def get_context(
    request: Request,
) -> FastAPIAppContext:
    return request.state.context


async def get_async_db_session(
    sessionmaker: Annotated[async_sessionmaker[AsyncSession], Depends(get_async_sessionmaker)],
) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker() as session:
        yield session


async def get_openai_chat_client(
    request: Request,
) -> OpenAIClient:
    """Get the OpenAI chat client"""
    return OpenAIClient(client=request.state.chat_client)


async def get_openai_embed_client(
    request: Request,
) -> OpenAIClient:
    """Get the OpenAI embed client"""
    return OpenAIClient(client=request.state.embed_client)


CommonDeps = Annotated[FastAPIAppContext, Depends(get_context)]
DBSession = Annotated[AsyncSession, Depends(get_async_db_session)]
ChatClient = Annotated[OpenAIClient, Depends(get_openai_chat_client)]
EmbeddingsClient = Annotated[OpenAIClient, Depends(get_openai_embed_client)]
