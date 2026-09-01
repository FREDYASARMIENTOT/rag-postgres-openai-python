from typing import Optional, TypedDict

from openai import AsyncOpenAI


# =============================================================================
# MAPA DE MODELOS DE EMBEDDING Y SOPORTE DE DIMENSIONES
# =============================================================================
# Cada modelo de embedding soporta o no la reducción de dimensiones
# mediante el parámetro `dimensions` en la API de OpenAI.
#
# Modelos que soportan dimensions:
#   - text-embedding-3-small (hasta 1536)
#   - text-embedding-3-large (hasta 3072, pero usamos 1024)
#
# Modelos que NO soportan dimensions (usar siempre la dimensión completa):
#   - text-embedding-ada-002 (fijo 1536)
#
# Para otros modelos no listados aquí, asumir que NO soportan dimensions
# a menos que se verifique explícitamente en la documentación de OpenAI.
# =============================================================================

MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES = frozenset({
    "text-embedding-3-small",
    "text-embedding-3-large",
})
"""Conjunto de modelos que aceptan el parámetro `dimensions` en la API de embeddings."""

# Requisito pendiente (Fase 3):
#   - Verificar si gpt-4o-mini (deployment: sii-supervisor-gpt-4o-mini)
#     en Modelo-IA-UR soporta el endpoint /embeddings.
#   - Si no soporta, desplegar text-embedding-3-large en Modelo-IA-UR
#     o crear recurso Azure OpenAI dedicado.
#   - Pendiente de autorización.


async def compute_text_embedding(
    texto_consulta: str,
    cliente_openai: AsyncOpenAI,
    modelo_embedding: str,
    deployment_embedding: Optional[str] = None,
    dimensiones_embedding: Optional[int] = None,
) -> list[float]:
    """
    Genera un vector de embedding para el texto de consulta dado.

    Este es el punto de entrada único para la generación de embeddings
    en toda la aplicación. Todas las rutas de código que necesiten
    convertir texto a vector deben pasar por esta función.

    Args:
        texto_consulta: Texto del cual generar el embedding.
        cliente_openai: Cliente OpenAI (AsyncOpenAI) configurado.
        modelo_embedding: Nombre del modelo de embeddings a utilizar.
        deployment_embedding: Nombre del deployment (solo Azure) o None.
        dimensiones_embedding: Dimensiones deseadas (solo para modelos
                               que soportan el parámetro `dimensions`).

    Returns:
        Lista de floats con el vector de embedding.

    Raises:
        ValueError: Si el modelo requiere dimensiones y no se proporcionan.
        openai.APIError: Si el API de OpenAI/Azure OpenAI no responde
                         o el deployment no existe.

    Dependencias externas:
        - OpenAI API (o Azure OpenAI vía AsyncOpenAI con base_url personalizado).
        - El deployment debe existir en el recurso configurado.

    Ejemplo:
        >>> vector = await compute_text_embedding(
        ...     "¿Qué documentos tratan sobre admisiones?",
        ...     cliente_openai,
        ...     modelo_embedding="text-embedding-3-large",
        ...     deployment_embedding="text-embedding-3-large",
        ...     dimensiones_embedding=1024,
        ... )
    """
    class ArgumentosExtra(TypedDict, total=False):
        dimensions: int

    argumentos_dimension: ArgumentosExtra = {}
    if modelo_embedding in MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES:
        if dimensiones_embedding is None:
            raise ValueError(
                f"El modelo de embeddings '{modelo_embedding}' requiere "
                "que se especifique el número de dimensiones. "
                "Configure AZURE_OPENAI_EMBED_DIMENSIONS o similar."
            )
        argumentos_dimension = {"dimensions": dimensiones_embedding}
    elif dimensiones_embedding is not None:
        # El modelo no soporta dimensions, pero se proporcionó.
        # Ignorar silenciosamente para compatibilidad.
        pass

    # Azure OpenAI toma el nombre del deployment como nombre del modelo.
    # OpenAI.com toma el nombre del modelo directamente.
    nombre_modelo_para_api = deployment_embedding if deployment_embedding else modelo_embedding

    embedding = await cliente_openai.embeddings.create(
        model=nombre_modelo_para_api,
        input=texto_consulta,
        **argumentos_dimension,
    )
    return embedding.data[0].embedding
