import logging
import os

import azure.identity.aio
import openai

logger = logging.getLogger("ragapp")

# =============================================================================
# CONSTANTES DE AUTH
# =============================================================================

SCOPE_AZURE_COGNITIVE = "https://cognitiveservices.azure.com/.default"
"""Scope de autenticación para Azure Cognitive Services (incluyendo Azure OpenAI)."""

SCOPE_FOUNDRY_MODELS = "https://ml.azure.com/.default"
"""Scope de autenticación para modelos desplegados en Foundry (Azure AI Studio)."""


# =============================================================================
# HELPERS
# =============================================================================


def _crear_cliente_openai_foundry(
    azure_credential: azure.identity.aio.AzureDeveloperCliCredential
    | azure.identity.aio.ManagedIdentityCredential
    | None,
    endpoint_var: str,
    deploy_var: str,
    servicio: str,
) -> openai.AsyncOpenAI:
    """Crea un cliente OpenAI apuntando a Foundry (Azure AI Studio) como endpoint.

    Foundry expone modelos desplegados via el endpoint OpenAI v1 del recurso
    de AI Services (Modelo-IA-UR). Usa la misma convención de URL que Azure
    OpenAI pero apuntando al endpoint de Foundry configurado.

    Args:
        azure_credential: Credencial Azure Identity (Managed Identity o CLI).
        endpoint_var: Nombre de variable de entorno para el endpoint.
        deploy_var: Nombre de variable de entorno para el deployment.
        servicio: Nombre descriptivo (chat/embeddings) para logs.

    Returns:
        AsyncOpenAI configurado para Foundry.
    """
    endpoint = os.environ[endpoint_var]
    deployment = os.environ[deploy_var]
    if api_key := os.getenv("AZURE_OPENAI_KEY"):
        logger.info(
            "Setting up Foundry client for %s using API key, endpoint %s, deployment %s",
            servicio,
            endpoint,
            deployment,
        )
        return openai.AsyncOpenAI(
            base_url=f"{endpoint.rstrip('/')}/openai/v1/",
            api_key=api_key,
        )
    elif azure_credential:
        logger.info(
            "Setting up Foundry client for %s using Azure Identity, endpoint %s, deployment %s",
            servicio,
            endpoint,
            deployment,
        )
        token_provider = azure.identity.aio.get_bearer_token_provider(
            azure_credential, SCOPE_AZURE_COGNITIVE
        )
        return openai.AsyncOpenAI(
            base_url=f"{endpoint.rstrip('/')}/openai/v1/",
            api_key=token_provider,
        )
    else:
        raise ValueError(
            f"Foundry client for {servicio} requires either an API key or Azure Identity credential."
        )


async def create_openai_chat_client(
    azure_credential: azure.identity.aio.AzureDeveloperCliCredential
    | azure.identity.aio.ManagedIdentityCredential
    | None,
) -> openai.AsyncOpenAI:
    openai_chat_client: openai.AsyncOpenAI
    OPENAI_CHAT_HOST = os.getenv("OPENAI_CHAT_HOST")
    if OPENAI_CHAT_HOST == "azure":
        azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        azure_deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
        if api_key := os.getenv("AZURE_OPENAI_KEY"):
            logger.info(
                "Setting up Azure OpenAI client for chat using API key, endpoint %s, deployment %s",
                azure_endpoint,
                azure_deployment,
            )
            openai_chat_client = openai.AsyncOpenAI(
                base_url=f"{azure_endpoint.rstrip('/')}/openai/v1/",
                api_key=api_key,
            )
        elif azure_credential:
            logger.info(
                "Setting up Azure OpenAI client for chat using Azure Identity, endpoint %s, deployment %s",
                azure_endpoint,
                azure_deployment,
            )
            token_provider = azure.identity.aio.get_bearer_token_provider(
                azure_credential, "https://cognitiveservices.azure.com/.default"
            )
            openai_chat_client = openai.AsyncOpenAI(
                base_url=f"{azure_endpoint.rstrip('/')}/openai/v1/",
                api_key=token_provider,
            )
        else:
            raise ValueError("Azure OpenAI client requires either an API key or Azure Identity credential.")
    elif OPENAI_CHAT_HOST == "foundry":
        openai_chat_client = _crear_cliente_openai_foundry(
            azure_credential,
            endpoint_var="FOUNDRY_OPENAI_ENDPOINT",
            deploy_var="FOUNDRY_CHAT_DEPLOYMENT",
            servicio="chat",
        )
    elif OPENAI_CHAT_HOST == "ollama":
        logger.info("Setting up OpenAI client for chat using Ollama")
        openai_chat_client = openai.AsyncOpenAI(
            base_url=os.getenv("OLLAMA_ENDPOINT"),
            api_key="nokeyneeded",
        )
    else:
        logger.info("Setting up OpenAI client for chat using OpenAI.com API key")
        openai_chat_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAICOM_KEY"))

    return openai_chat_client


async def create_openai_embed_client(
    azure_credential: azure.identity.aio.AzureDeveloperCliCredential
    | azure.identity.aio.ManagedIdentityCredential
    | None,
    host_override: Optional[str] = None,
    deployment_override: Optional[str] = None,
) -> openai.AsyncOpenAI:
    openai_embed_client: openai.AsyncOpenAI
    host = host_override if host_override is not None else os.getenv("OPENAI_EMBED_HOST")
    if host == "azure":
        azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        azure_deployment = os.environ["AZURE_OPENAI_EMBED_DEPLOYMENT"]
        if api_key := os.getenv("AZURE_OPENAI_KEY"):
            logger.info(
                "Setting up Azure OpenAI client for embeddings using API key, endpoint %s, deployment %s",
                azure_endpoint,
                azure_deployment,
            )
            openai_embed_client = openai.AsyncOpenAI(
                base_url=f"{azure_endpoint.rstrip('/')}/openai/v1/",
                api_key=api_key,
            )
        elif azure_credential:
            logger.info(
                "Setting up Azure OpenAI client for embeddings using Azure Identity, endpoint %s, deployment %s",
                azure_endpoint,
                azure_deployment,
            )
            token_provider = azure.identity.aio.get_bearer_token_provider(
                azure_credential, "https://cognitiveservices.azure.com/.default"
            )
            openai_embed_client = openai.AsyncOpenAI(
                base_url=f"{azure_endpoint.rstrip('/')}/openai/v1/",
                api_key=token_provider,
            )
        else:
            raise ValueError("Azure OpenAI client requires either an API key or Azure Identity credential.")
    elif host == "foundry":
        deploy_name = deployment_override if deployment_override is not None else \
            os.environ.get("FOUNDRY_EMBEDDING_DEPLOYMENT", "unknown")
        logger.info(
            "Setting up Foundry client for embeddings, deployment %s",
            deploy_name,
        )
        endpoint = os.environ["FOUNDRY_OPENAI_ENDPOINT"]
        if api_key := os.getenv("AZURE_OPENAI_KEY"):
            openai_embed_client = openai.AsyncOpenAI(
                base_url=f"{endpoint.rstrip('/')}/openai/v1/",
                api_key=api_key,
            )
        elif azure_credential:
            token_provider = azure.identity.aio.get_bearer_token_provider(
                azure_credential, SCOPE_AZURE_COGNITIVE
            )
            openai_embed_client = openai.AsyncOpenAI(
                base_url=f"{endpoint.rstrip('/')}/openai/v1/",
                api_key=token_provider,
            )
        else:
            raise ValueError(
                "Foundry client for embeddings requires either an API key "
                "or Azure Identity credential."
            )
    elif host == "ollama":
        logger.info("Setting up OpenAI client for embeddings using Ollama")
        openai_embed_client = openai.AsyncOpenAI(
            base_url=os.getenv("OLLAMA_ENDPOINT"),
            api_key="nokeyneeded",
        )
    else:
        logger.info("Setting up OpenAI client for embeddings using OpenAI.com API key")
        openai_embed_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAICOM_KEY"))
    return openai_embed_client
