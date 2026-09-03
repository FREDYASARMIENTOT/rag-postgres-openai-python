import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional, TypedDict

import fastapi
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv
from openai import AsyncOpenAI
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_app.dependencies import (
    FastAPIAppContext,
    common_parameters,
    create_async_sessionmaker,
    get_azure_credential,
)
from fastapi_app.openai_clients import create_openai_chat_client, create_openai_embed_client
from fastapi_app.postgres_engine import create_postgres_engine_from_env
from fastapi_app.proveedores import crear_proveedor_embeddings, crear_proveedor_llm

logger = logging.getLogger("ragapp")


# State is set directly on app.state in lifespan (FastAPI 0.129+ / Starlette 0.52+)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    context = await common_parameters()
    azure_credential = None
    if (
        os.getenv("OPENAI_CHAT_HOST") == "azure"
        or os.getenv("OPENAI_EMBED_HOST") == "azure"
        or os.getenv("POSTGRES_HOST", "").endswith(".database.azure.com")
    ):
        azure_credential = await get_azure_credential()
    engine = await create_postgres_engine_from_env(azure_credential)
    sessionmaker = await create_async_sessionmaker(engine)
    chat_client = await create_openai_chat_client(azure_credential)
    embed_client = await create_openai_embed_client(azure_credential)
    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

    # ── RAG Institucional: crear proveedores (reutilizables entre requests) ──
    proveedor_embeddings = None
    proveedor_llm = None
    try:
        rag_embed_client = await create_openai_embed_client(
            azure_credential,
            host_override="foundry",
            deployment_override=context.rag_embed_deployment or context.rag_embed_model,
        )
        proveedor_embeddings = crear_proveedor_embeddings(
            cliente=rag_embed_client,
            modelo=context.rag_embed_model,
            deployment=context.rag_embed_deployment,
            dimensiones=context.rag_embed_dimensions,
        )
        logger.info("RAG Institucional: proveedor embeddings creado")
    except Exception as e:
        logger.warning("RAG Institucional: no se pudo crear proveedor embeddings: %s", e)

    try:
        rag_chat_client = await create_openai_chat_client(
            azure_credential,
            host_override="foundry",
            deployment_override=context.rag_llm_deployment or context.rag_llm_model,
        )
        proveedor_llm = crear_proveedor_llm(
            cliente=rag_chat_client,
            modelo=context.rag_llm_model,
            deployment=context.rag_llm_deployment,
        )
        logger.info("RAG Institucional: proveedor LLM creado")
    except Exception as e:
        logger.warning("RAG Institucional: no se pudo crear proveedor LLM: %s", e)

    # Set state on app.state so routes can access via request.app.state
    app.state.sessionmaker = sessionmaker
    app.state.context = context
    app.state.chat_client = chat_client
    app.state.embed_client = embed_client
    app.state.rag_proveedor_embeddings = proveedor_embeddings
    app.state.rag_proveedor_llm = proveedor_llm

    yield
    await engine.dispose()


def create_app(testing: bool = False):
    if os.getenv("RUNNING_IN_PRODUCTION"):
        logging.basicConfig(level=logging.INFO)
    else:
        if not testing:
            load_dotenv(override=True)
        logging.basicConfig(level=logging.INFO)

    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)

    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        logger.info("Configuring Azure Monitor")
        configure_azure_monitor(logger_name="ragapp")
        OpenAIInstrumentor().instrument()

    app = fastapi.FastAPI(docs_url="/docs", lifespan=lifespan)

    from fastapi_app.routes import api_routes, frontend_routes
    from fastapi_app.rag_routes import router as rag_router

    app.include_router(api_routes.router)
    app.include_router(rag_router)
    app.mount("/", frontend_routes.router)

    return app
