"""
Punto de entrada para ejecutar el MCP Server del RAG Institucional.

Propósito:
    Configura las dependencias (repositorio, servicios, cliente OpenAI)
    desde variables de entorno e inicia el servidor MCP con transporte
    stdio, listo para ser consumido por un cliente MCP.

Uso:
    python -m fastapi_app.mcp_servidor_main

    O mediante un cliente MCP configurado como:
    ```json
    {
      "mcpServers": {
        "rag-institucional": {
          "command": "python",
          "args": ["-m", "fastapi_app.mcp_servidor_main"]
        }
      }
    }
    ```

Contexto arquitectónico:
    Este módulo es la frontera entre el mundo externo (agente/cliente MCP)
    y los servicios internos del RAG. Se encarga de:
    1. Cargar configuración (.env, variables de entorno).
    2. Crear engine PostgreSQL + sesión.
    3. Inicializar repositorio y servicios.
    4. Crear e iniciar servidor MCP con transporte stdio.

    En modo desarrollo, el servidor se ejecuta en el mismo proceso que
    el cliente. En producción, se ejecutaría como un proceso separado
    (Container App, Function, etc.).

Transporte:
    - stdio: Para pruebas locales y desarrollo.
    - Streamable HTTP: Para despliegue en Azure (futuro).

Seguridad:
    - Lee secretos de variables de entorno (nunca hardcodeados).
    - La autenticación Azure usa Managed Identity cuando está disponible.
    - No expone el servidor a la red en modo stdio.

RESTRICCIONES:
    - Requiere PostgreSQL con pgvector habilitado.
    - Requiere conexión a Azure AI Foundry (o mock para tests).
    - Si no hay BD disponible, el servidor no arranca.
"""

from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from fastapi_app.dependencies import (
    common_parameters,
    create_async_sessionmaker,
    get_azure_credential,
)
from fastapi_app.mcp_servidor import crear_mcp_servidor
from fastapi_app.openai_clients import create_openai_chat_client, create_openai_embed_client
from fastapi_app.postgres_engine import create_postgres_engine_from_env
from fastapi_app.proveedores import crear_proveedor_embeddings, crear_proveedor_llm
from fastapi_app.repositorio_documentos import RepositorioDocumentos
from fastapi_app.servicio_generacion import ServicioGeneracion
from fastapi_app.servicio_ingesta import ServicioIngesta
from fastapi_app.servicio_retrieval import ServicioRetrieval

logger = logging.getLogger("ragapp")


async def main():
    """Función principal que inicializa y ejecuta el MCP Server."""
    # Cargar variables de entorno
    load_dotenv(override=True)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)

    logger.info("Iniciando MCP Server del RAG Institucional UR...")

    # Cargar configuración desde common_parameters() (reusa FastAPIAppContext)
    config = await common_parameters()
    logger.info(
        "Config RAG: embed_model=%s embed_dim=%d llm=%s",
        config.rag_embed_model, config.rag_embed_dimensions, config.rag_llm_model,
    )

    # Obtener credencial Azure (si aplica)
    azure_credential = None
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    if postgres_host.endswith(".database.azure.com"):
        azure_credential = await get_azure_credential()

    # Crear engine PostgreSQL y sessionmaker
    engine = await create_postgres_engine_from_env(azure_credential)
    sessionmaker = await create_async_sessionmaker(engine)

    # Crear cliente de embeddings para Foundry con deployment RAG
    embed_client = None
    try:
        embed_client = await create_openai_embed_client(
            azure_credential,
            host_override="foundry",
            deployment_override=config.rag_embed_deployment or config.rag_embed_model,
        )
        logger.info("Cliente de embeddings Foundry creado exitosamente.")
    except Exception as e:
        logger.warning(
            "No se pudo crear el cliente de embeddings: %s. "
            "La ingesta no generará embeddings.",
            e,
        )

    # Crear proveedor de embeddings encapsulado
    proveedor_embeddings = None
    if embed_client:
        proveedor_embeddings = crear_proveedor_embeddings(
            cliente=embed_client,
            modelo=config.rag_embed_model,
            deployment=config.rag_embed_deployment,
            dimensiones=config.rag_embed_dimensions,
        )

    # Crear cliente de chat para Foundry con Luna
    chat_client = None
    proveedor_llm = None
    try:
        chat_client = await create_openai_chat_client(
            azure_credential,
            host_override="foundry",
            deployment_override=config.rag_llm_deployment or config.rag_llm_model,
        )
        logger.info("Cliente de chat Foundry (Luna) creado exitosamente.")
        proveedor_llm = crear_proveedor_llm(
            cliente=chat_client,
            modelo=config.rag_llm_model,
            deployment=config.rag_llm_deployment,
        )
    except Exception as e:
        logger.warning(
            "No se pudo crear el cliente de chat Foundry: %s. "
            "La generacion RAG no estara disponible.",
            e,
        )

    # Crear repositorio y servicios con sesión
    async with sessionmaker() as session:
        repositorio = RepositorioDocumentos(session)
        servicio_ingesta = ServicioIngesta(
            repositorio=repositorio,
            proveedor_embeddings=proveedor_embeddings,
        )
        servicio_retrieval = ServicioRetrieval(
            repositorio=repositorio,
            proveedor_embeddings=proveedor_embeddings,
        )
        servicio_generacion = None
        if proveedor_llm:
            servicio_generacion = ServicioGeneracion(
                servicio_retrieval=servicio_retrieval,
                proveedor_llm=proveedor_llm,
            )
            logger.info("ServicioGeneracion inicializado con %s/%s", proveedor_llm.modelo, proveedor_llm.deployment)

        # Crear y ejecutar servidor MCP
        mcp = crear_mcp_servidor(
            repositorio=repositorio,
            servicio_ingesta=servicio_ingesta,
            servicio_retrieval=servicio_retrieval,
            servicio_generacion=servicio_generacion,
            nombre="UR-RAG-MCP-Server",
        )

        logger.info("MCP Server listo. Iniciando con transporte stdio...")
        try:
            # Ejecutar con transporte stdio (bloqueante hasta que el cliente cierre)
            await mcp.run_stdio_async()
        except KeyboardInterrupt:
            logger.info("MCP Server detenido por el usuario.")
        finally:
            await engine.dispose()
            logger.info("Conexión PostgreSQL cerrada.")


if __name__ == "__main__":
    asyncio.run(main())