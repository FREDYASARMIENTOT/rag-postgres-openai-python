from typing import Optional, Union

import numpy as np
from openai import AsyncAzureOpenAI, AsyncOpenAI
from sqlalchemy import Float, Integer, column, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_app.api_models import Filter
from fastapi_app.embeddings import compute_text_embedding
from fastapi_app.postgres_models import Item


# =============================================================================
# LISTAS BLANCAS DE SEGURIDAD PARA CONSTRUCCIÓN DE FILTROS SQL
# =============================================================================
# Los nombres de columna y operadores que vienen del agente LLM (AdvancedRAGChat)
# deben validarse contra listas blancas para evitar inyección SQL.
# El agente puede generar solicitudes como:
#   {"column": "price", "comparison_operator": ">", "value": 30.0}
# Sin validación, un agente comprometido o prompt injection podría inyectar:
#   {"column": "price; DROP TABLE items; --", "comparison_operator": ">", "value": 0}
# =============================================================================

COLUMNAS_FILTRO_PERMITIDAS = frozenset({"price", "brand", "type", "name"})
"""Columnas de la tabla `items` que pueden ser filtradas externamente por el agente LLM."""

OPERADORES_FILTRO_PERMITIDOS = frozenset({">", "<", ">=", "<=", "=", "!="})
"""Operadores de comparación SQL permitidos para filtros generados por agente LLM."""


class PostgresSearcher:
    """
    Motor de búsqueda para el RAG Institucional.

    Separa la lógica de búsqueda (vectorial, textual o híbrida)
    de la generación de respuestas y de la gestión de embeddings.

    Responsabilidades:
    - Construir consultas SQL seguras contra la tabla `items`.
    - Invocar al API de embeddings para convertir consultas en vectores.
    - Combinar resultados de búsqueda vectorial y textual (híbrido RRF).
    - Devolver modelos SQLAlchemy listos para serialización.

    Dependencias externas:
    - PostgreSQL con extensión pgvector (para distancia coseno <=>).
    - OpenAI/Azure OpenAI API para embeddings (modelo configurable).
    - Tabla `items` con columna vectorial configurable (AZURE_OPENAI_EMBEDDING_COLUMN).
    """

    def __init__(
        self,
        db_session: AsyncSession,
        openai_embed_client: Union[AsyncOpenAI, AsyncAzureOpenAI],
        embed_deployment: Optional[str],  # Not needed for non-Azure OpenAI or for retrieval_mode="text"
        embed_model: str,
        embed_dimensions: Optional[int],
        embedding_column: str,
    ):
        """
        Inicializa el buscador con sesión de base de datos y configuración de embeddings.

        Args:
            db_session: Sesión asíncrona de SQLAlchemy para PostgreSQL.
            openai_embed_client: Cliente OpenAI/Azure OpenAI para generar embeddings.
            embed_deployment: Nombre del deployment de embeddings (Azure) o None.
            embed_model: Nombre del modelo de embeddings (ej: text-embedding-3-large).
            embed_dimensions: Dimensiones del vector de embedding (ej: 1024, 768).
            embedding_column: Nombre de la columna vectorial en la tabla `items`.

        Seguridad:
            - embed_deployment solo se usa como nombre de modelo en la API; no se interpola en SQL.
            - embedding_column se usa directamente en SQL, debe ser validado externamente.
        """
        self.db_session = db_session
        self.openai_embed_client = openai_embed_client
        self.embed_model = embed_model
        self.embed_deployment = embed_deployment
        self.embed_dimensions = embed_dimensions
        self.embedding_column = embedding_column

    def build_filter_clause(self, filters: Optional[list[Filter]]) -> tuple[str, str]:
        """
        Construye cláusulas WHERE/AND para filtrar resultados en PostgreSQL.

        VALIDA nombres de columna y operadores contra LISTAS BLANCAS
        para prevenir inyección SQL desde el agente LLM.

        Args:
            filters: Lista opcional de filtros generados por el agente LLM.
                     Cada filtro tiene: column, comparison_operator, value.

        Returns:
            Tupla (clausula_where, clausula_and) para incorporar en consultas SQL.
            Ejemplo: ('WHERE price > 30', 'AND price > 30')

        Seguridad:
            - Los nombres de columna se validan contra COLUMNAS_FILTRO_PERMITIDAS.
            - Los operadores se validan contra OPERADORES_FILTRO_PERMITIDOS.
            - Los valores se escapan para strings (comillas simples escapadas).
            - Si un filtro no pasa validación, se omite silenciosamente (no se lanza error).

        Riesgo residual conocido:
            - embedding_column se usa directamente en SQL por ser configurado
              administrativamente, no por el agente LLM.
        """
        if not filters:
            return "", ""
        filter_clauses = []
        for filtro in filters:
            # Validar nombre de columna contra lista blanca
            if filtro.column not in COLUMNAS_FILTRO_PERMITIDAS:
                # Omitir filtros con columnas no autorizadas en lugar de fallar
                continue
            # Validar operador contra lista blanca
            if filtro.comparison_operator not in OPERADORES_FILTRO_PERMITIDOS:
                continue
            # Escapar valor para evitar inyección: comillas simples duplicadas
            if isinstance(filtro.value, str):
                valor_seguro = f"'{filtro.value.replace(chr(39), chr(39)*2)}'"
            else:
                valor_seguro = str(filtro.value)
            filter_clauses.append(f"{filtro.column} {filtro.comparison_operator} {valor_seguro}")
        if not filter_clauses:
            return "", ""
        filter_clause = " AND ".join(filter_clauses)
        return f"WHERE {filter_clause}", f"AND {filter_clause}"

    async def search(
        self,
        query_text: Optional[str],
        query_vector: list[float],
        top: int = 5,
        filters: Optional[list[Filter]] = None,
    ) -> list[Item]:
        """
        Ejecuta búsqueda vectorial, textual o híbrida en PostgreSQL.

        Modos de búsqueda (seleccionados automáticamente según los argumentos):

        1. **Híbrido (vectorial + textual):** Cuando query_text y query_vector tienen datos.
           Usa Reciprocal Rank Fusion (RRF) con k=60 para combinar rankings.

        2. **Vectorial puro:** Cuando SOLO query_vector tiene datos.
           Usa distancia coseno (<=>) con la columna embedding_column.

        3. **Textual pura:** Cuando SOLO query_text tiene datos.
           Usa búsqueda full-text en inglés sobre la columna 'description'.

        Args:
            query_text: Texto para búsqueda full-text (inglés). None si solo vectorial.
            query_vector: Vector de embedding para búsqueda por similitud.
            top: Número máximo de resultados a retornar.
            filters: Filtros validados contra listas blancas de seguridad.

        Returns:
            Lista de modelos Item (SQLAlchemy) con los resultados.

        Restricciones:
            - Requiere pgvector habilitado en PostgreSQL (para búsqueda vectorial).
            - Requiere índice GIN en to_tsvector('english', description) para full-text.
            - La columna vectorial debe coincidir con embedding_column configurada.

        Seguridad:
            - Los filtros ya fueron validados contra listas blancas en build_filter_clause().
            - embedding_column se interpola directamente por ser configuración administrativa.
            - Los parámetros de la consulta se pasan como bind parameters (:embedding, :query, :k).
        """
        filter_clause_where, filter_clause_and = self.build_filter_clause(filters)
        table_name = Item.__tablename__
        vector_query = f"""
            SELECT id, RANK () OVER (ORDER BY {self.embedding_column} <=> :embedding) AS rank
                FROM {table_name}
                {filter_clause_where}
                ORDER BY {self.embedding_column} <=> :embedding
                LIMIT 20
            """

        fulltext_query = f"""
            SELECT id, RANK () OVER (ORDER BY ts_rank_cd(to_tsvector('english', description), query) DESC)
                FROM {table_name}, plainto_tsquery('english', :query) query
                WHERE to_tsvector('english', description) @@ query {filter_clause_and}
                ORDER BY ts_rank_cd(to_tsvector('english', description), query) DESC
                LIMIT 20
            """

        hybrid_query = f"""
        WITH vector_search AS (
            {vector_query}
        ),
        fulltext_search AS (
            {fulltext_query}
        )
        SELECT
            COALESCE(vector_search.id, fulltext_search.id) AS id,
            COALESCE(1.0 / (:k + vector_search.rank), 0.0) +
            COALESCE(1.0 / (:k + fulltext_search.rank), 0.0) AS score
        FROM vector_search
        FULL OUTER JOIN fulltext_search ON vector_search.id = fulltext_search.id
        ORDER BY score DESC
        LIMIT 20
        """

        if query_text is not None and len(query_vector) > 0:
            sql = text(hybrid_query).columns(column("id", Integer), column("score", Float))
        elif len(query_vector) > 0:
            sql = text(vector_query).columns(column("id", Integer), column("rank", Integer))
        elif query_text is not None:
            sql = text(fulltext_query).columns(column("id", Integer), column("rank", Integer))
        else:
            raise ValueError(
                "No se puede ejecutar la búsqueda: tanto el texto como el vector están vacíos. "
                "Se requiere al menos uno de los dos modos de búsqueda."
            )

        results = (
            await self.db_session.execute(
                sql,
                {"embedding": np.array(query_vector), "query": query_text, "k": 60},
            )
        ).fetchall()

        # Convert results to SQLAlchemy models
        row_models = []
        for id, _ in results[:top]:
            item = await self.db_session.execute(select(Item).where(Item.id == id))
            row_models.append(item.scalar())
        return row_models

    async def search_and_embed(
        self,
        query_text: Optional[str] = None,
        top: int = 5,
        enable_vector_search: bool = False,
        enable_text_search: bool = False,
        filters: Optional[list[Filter]] = None,
    ) -> list[Item]:
        """
        Punto de entrada principal para búsqueda con generación automática de embeddings.

        Orquesta el flujo:
        1. Si enable_vector_search está activo: genera embedding vía API OpenAI/Azure.
        2. Si enable_text_search está activo: conserva el texto original.
        3. Delega en search() para ejecutar la consulta combinada.

        Args:
            query_text: Consulta del usuario en lenguaje natural.
            top: Número máximo de resultados.
            enable_vector_search: Si True, genera embedding y habilita búsqueda vectorial.
            enable_text_search: Si True, habilita búsqueda full-text.
            filters: Filtros adicionales (validados contra listas blancas internamente).

        Returns:
            Lista de modelos Item con los documentos más relevantes.

        Dependencias externas:
            - compute_text_embedding(): llama a OpenAI/Azure OpenAI API.
              Si el deployment de embeddings no existe, esta llamada fallará
              con un error claro del API (no un error genérico de conexión).
        """
        vector: list[float] = []
        if enable_vector_search and query_text is not None:
            vector = await compute_text_embedding(
                query_text,
                self.openai_embed_client,
                self.embed_model,
                self.embed_deployment,
                self.embed_dimensions,
            )
        if not enable_text_search:
            query_text = None

        return await self.search(query_text, vector, top, filters)
