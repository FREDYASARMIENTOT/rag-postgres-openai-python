import asyncio
import logging
import os

from azure.identity import AzureDeveloperCliCredential
from pgvector.asyncpg import register_vector
from sqlalchemy import event, text
from sqlalchemy.engine import AdaptedConnection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from fastapi_app.dependencies import get_azure_credential

logger = logging.getLogger("ragapp")


# =============================================================================
# VALIDACIÓN DE REQUISITOS DE PGVECTOR EN POSTGRESQL
# =============================================================================
# Antes de que la aplicación pueda usar columnas vectoriales (pgvector),
# la extensión `vector` debe estar habilitada en la base de datos PostgreSQL.
#
# La validación se realiza en dos momentos:
# 1. Al registrar el tipo vector en la conexión (register_vector).
# 2. (Opcional) Consultando pg_available_extensions para verificar disponibilidad.
#
# Estado actual de supersetdev:
#   La extensión `vector` NO está habilitada en PostgreSQL.
#   Se requiere la siguiente operación (post-despliegue):
#     CREATE EXTENSION vector;
# =============================================================================


async def verify_pgvector_available(engine: AsyncEngine) -> bool:
    """
    Verifica si la extensión pgvector está disponible en PostgreSQL.

    Consulta pg_available_extensions para determinar si el paquete
    `vector` está instalado en el servidor PostgreSQL, independientemente
    de si está habilitado en la base de datos actual.

    Esta función es útil para diagnóstico temprano sin modificar la BD.

    Returns:
        True si la extensión `vector` está disponible (instalada en el servidor).
        False si no está disponible.

    Nota:
        - Disponible ≠ Habilitada. La extensión puede estar instalada
          en el servidor pero no creada en la base de datos actual.
        - Para habilitar: CREATE EXTENSION vector (requiere privilegios).
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT TRUE FROM pg_available_extensions WHERE name = 'vector'")
        )
        return result.scalar() is not None


async def verify_pgvector_created(engine: AsyncEngine) -> bool:
    """
    Verifica si pgvector está habilitado (CREATE EXTENSION executado)
    en la base de datos actual.

    Returns:
        True si la extensión está creada en la BD actual.
        False si no está creada.

    Para habilitar: ejecutar CREATE EXTENSION vector;
    en la base de datos rag_institucional.
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT TRUE FROM pg_extension WHERE extname = 'vector'")
        )
        return result.scalar() is not None
    """Factory asíncrona que crea y configura un engine SQLAlchemy para PostgreSQL.

    Maneja dos modos de autenticación:
    1. **Token de Azure Identity** (Azure Database for PostgreSQL):
       - Se activa automáticamente si el host termina en `.database.azure.com`.
       - Obtiene token de acceso vía Azure AD (Managed Identity o DefaultAzureCredential).
       - Renueva el token automáticamente antes de cada conexión.
    2. **Contraseña directa** (PostgreSQL local/on-premise):
       - Usa la contraseña proporcionada via POSTGRES_PASSWORD.
       - Conexión directa sin Azure AD.

    Args:
        host: Hostname del servidor PostgreSQL.
        username: Nombre de usuario para autenticación.
        database: Nombre de la base de datos.
        password: Contraseña (o None si se usa token Azure).
        sslmode: Modo SSL ('require', 'prefer', 'disable') o None.
        azure_credential: Credencial Azure AD para token-based auth.

    Returns:
        AsyncEngine configurado con:
        - Event listener para registrar pgvector al conectar.
        - Event listener para renovar token Azure AD si corresponde.

    Raises:
        ValueError: Si el host es Azure y no se provee credencial.
    """
    async def get_password_from_azure_credential():
        token = await azure_credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        return token.token

    token_based_password = False
    if host.endswith(".database.azure.com"):
        token_based_password = True
        logger.info("Autenticando a Azure Database for PostgreSQL usando Azure Identity...")
        if azure_credential is None:
            raise ValueError(
                "Se requiere una credencial de Azure para autenticarse "
                "a Azure Database for PostgreSQL. Proporcione azure_credential "
                "o configure POSTGRES_HOST con un host no-Azure."
            )
        password = await get_password_from_azure_credential()
    else:
        logger.info("Autenticando a PostgreSQL usando contraseña...")

    DATABASE_URI = f"postgresql+asyncpg://{username}:{password}@{host}/{database}"
    if sslmode:
        DATABASE_URI += f"?ssl={sslmode}"

    engine = create_async_engine(DATABASE_URI, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def register_custom_types(dbapi_connection: AdaptedConnection, *args):
        """
        Registra el tipo de datos `vector` de pgvector en la conexión asyncpg.

        Este hook se ejecuta cada vez que SQLAlchemy establece una conexión
        nueva con PostgreSQL.

        Maneja gracefulmente el caso en que pgvector no está habilitado:
        - Si register_vector falla con ValueError, se registra una advertencia.
        - La aplicación puede operar sin pgvector (búsqueda full-text sola).
        - Para búsqueda vectorial, pgvector debe estar habilitado.

        Ver ARCHITECTURA-RAG.md -> pgvector para procedimiento de habilitación.
        """
        logger.info("Registrando tipo vector de pgvector en la conexión...")
        try:
            dbapi_connection.run_async(register_vector)
        except ValueError:
            logger.warning(
                "No se pudo registrar el tipo de dato 'vector' de pgvector. "
                "La extensión 'vector' no ha sido creada en esta base de datos. "
                "Ejecute: CREATE EXTENSION vector; en la base de datos '%s'. "
                "La aplicación funcionará sin búsqueda vectorial hasta que pgvector esté habilitado.",
                database,
            )

    @event.listens_for(engine.sync_engine, "do_connect")
    def update_password_token(dialect, conn_rec, cargs, cparams):
        """
        Renueva el token de Azure AD antes de cada conexión.

        Esto es necesario porque los tokens de Azure AD tienen una validez
        limitada (~24 horas para Managed Identity, ~1 hora para DefaultAzureCredential).
        Sin este hook, las conexiones fallarían después de expirar el token.
        """
        if token_based_password:
            logger.info("Renovando token de acceso para Azure Database for PostgreSQL...")
            loop = asyncio.get_event_loop()
            cparams["password"] = loop.run_until_complete(get_password_from_azure_credential())

    return engine


async def create_postgres_engine_from_env(azure_credential=None) -> AsyncEngine:
    """
    Crea engine PostgreSQL a partir de variables de entorno.

    Variables de entorno requeridas:
        POSTGRES_HOST (str): Hostname del servidor.
        POSTGRES_USERNAME (str): Usuario de base de datos.

    Variables de entorno opcionales:
        POSTGRES_DATABASE (str): Nombre de la BD. Default: 'postgres'.
        POSTGRES_PASSWORD (str): Contraseña (no requerida si Azure AD).
        POSTGRES_SSL (str): Modo SSL ('require', 'prefer', 'disable').

    Auto-detección de Azure:
        Si POSTGRES_HOST termina en .database.azure.com, se intenta
        autenticación vía Azure AD automáticamente.

    Returns:
        AsyncEngine configurado.
    """
    if azure_credential is None and os.environ["POSTGRES_HOST"].endswith(".database.azure.com"):
        azure_credential = get_azure_credential()

    return await create_postgres_engine(
        host=os.environ["POSTGRES_HOST"],
        username=os.environ["POSTGRES_USERNAME"],
        database=os.environ["POSTGRES_DATABASE"],
        password=os.environ.get("POSTGRES_PASSWORD"),
        sslmode=os.environ.get("POSTGRES_SSL"),
        azure_credential=azure_credential,
    )


async def create_postgres_engine_from_args(args, azure_credential=None) -> AsyncEngine:
    """
    Crea engine PostgreSQL a partir de argumentos de línea de comandos.

    Args:
        args: Objeto con atributos: host, username, database, password, sslmode, tenant_id.
        azure_credential: Credencial Azure existente o None.

    Auto-detección de Azure:
        Si args.host termina en .database.azure.com, se intenta
        autenticación vía Azure AD con AzureDeveloperCliCredential.
        Si args.tenant_id está presente, se usa ese tenant.

    Returns:
        AsyncEngine configurado.
    """
    if azure_credential is None and args.host.endswith(".database.azure.com"):
        if tenant_id := args.tenant_id:
            logger.info("Authenticating to Azure using Azure Developer CLI Credential for tenant %s", tenant_id)
            azure_credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Authenticating to Azure using Azure Developer CLI Credential")
            azure_credential = AzureDeveloperCliCredential(process_timeout=60)

    return await create_postgres_engine(
        host=args.host,
        username=args.username,
        database=args.database,
        password=args.password,
        sslmode=args.sslmode,
        azure_credential=azure_credential,
    )
