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
#   - text-embedding-3-large (hasta 3072)
#
# Modelos que NO soportan dimensions (usar siempre la dimensión completa):
#   - text-embedding-ada-002 (fijo 1536)
#
# Para otros modelos no listados aquí, asumir que NO soportan dimensions
# a menos que se verifique explícitamente en la documentación de OpenAI.
#
# IMPORTANTE: Foundry (Azure AI Studio) NO soporta el parámetro `dimensions`.
# Cuando la dimensión solicitada sea la máxima del modelo (3072 para
# text-embedding-3-large), el código omite el envío de `dimensions`
# para compatibilidad con Foundry. Ver MODELOS_EMBEDDING_DIMENSIONES_MAXIMAS.
# =============================================================================

MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES = frozenset({
    "text-embedding-3-small",
    "text-embedding-3-large",
})
"""Conjunto de modelos que aceptan el parámetro `dimensions` en la API de embeddings."""

MODELOS_EMBEDDING_DIMENSIONES_MAXIMAS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}
"""Dimensión máxima nativa de cada modelo de embedding.

Cuando la dimensión solicitada coincide con la máxima del modelo,
no se envía el parámetro `dimensions` a la API. Esto permite
compatibilidad con Foundry (Azure AI Studio), que no soporta
dicho parámetro.

Uso:
    - Si dimensions < max -> se envía `dimensions=N` (reducción).
    - Si dimensions >= max -> NO se envía (API devuelve la máxima).
"""

# Decisión de embedding (Fase Foundry):
#   - Modelo seleccionado: text-embedding-3-large
#   - Deployment real: ur-rag-embedding-3-large
#   - Dimensiones: 3072 (completas, sin parámetro dimensions para Foundry)
#   - RAG Productos: text-embedding-3-large, 1024d (usa dimensions normalmente)


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
        deployment_embedding: Nombre del deployment (solo Azure/Foundry)
                              o None para OpenAI.com.
        dimensiones_embedding: Dimensiones deseadas. Para modelos que
                              soportan `dimensions` (text-embedding-3-*):
                              - Si es None: no se envía el parámetro,
                                la API devuelve la dimensión completa.
                              - Si es < máximo del modelo: se envía
                                `dimensions=N` para reducir la salida.
                              - Si es >= máximo del modelo: no se envía
                                (compatible con Foundry que no soporta
                                el parámetro `dimensions`).

    Returns:
        Lista de floats con el vector de embedding.

    Raises:
        openai.APIError: Si el API de OpenAI/Azure OpenAI no responde
                         o el deployment no existe.

    Dependencias externas:
        - OpenAI API (o Azure OpenAI vía AsyncOpenAI con base_url personalizado).
        - El deployment debe existir en el recurso configurado.
        - Foundry no soporta el parámetro `dimensions`; el código lo omite
          automáticamente cuando la dimensión solicitada es la máxima.

    Ejemplo:
        >>> vector = await compute_text_embedding(
        ...     "¿Qué documentos tratan sobre admisiones?",
        ...     cliente_openai,
        ...     modelo_embedding="text-embedding-3-large",
        ...     deployment_embedding="ur-rag-embedding-3-large",
        ...     dimensiones_embedding=3072,
        ... )
    """
    class ArgumentosExtra(TypedDict, total=False):
        dimensions: int

    argumentos_dimension: ArgumentosExtra = {}
    if modelo_embedding in MODELOS_EMBEDDING_CON_DIMENSIONES_CONFIGURABLES:
        if dimensiones_embedding is None:
            # Sin dimensions especificadas: no enviar parámetro.
            # La API devuelve la dimensión completa del modelo.
            # Esto permite compatibilidad con Foundry, que no soporta
            # el parámetro `dimensions` en la API de embeddings.
            pass
        else:
            dimension_maxima = MODELOS_EMBEDDING_DIMENSIONES_MAXIMAS.get(modelo_embedding)
            if dimension_maxima is not None and dimensiones_embedding < dimension_maxima:
                # Solo enviar dimensions si se solicita una reducción
                # respecto a la dimensión máxima del modelo.
                argumentos_dimension = {"dimensions": dimensiones_embedding}
            # Si dimensiones_embedding >= dimension_maxima, no enviar
            # dimensions (la API devuelve la dimensión máxima por defecto).
            # Esto es necesario para compatibilidad con Foundry.
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
