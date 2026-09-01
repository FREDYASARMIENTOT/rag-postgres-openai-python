"""
Proveedores de LLM y Embeddings para el RAG Institucional.

Define contratos abstractos (ProveedorLLM, ProveedorEmbeddings) que
desacoplan la lógica de negocio de modelos concretos como gpt-4o-mini
o text-embedding-3-small. Las implementaciones concretas obtienen los
identificadores de modelo y deployment desde configuración.

Principios:
- La lógica de negocio NUNCA contiene nombres de modelos hardcodeados.
- Los identificadores provienen exclusivamente de configuración.
- Cada proveedor maneja su propia autenticación y endpoint.
- Compatible con Azure OpenAI, Foundry (Azure AI Studio), y OpenAI.com.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

import openai

logger = logging.getLogger("ragapp")


# =============================================================================
# INTERFACES / CONTRATOS
# =============================================================================


class ProveedorLLM(ABC):
    """Contrato abstracto para proveedores de LLM (chat/completions).

    Cualquier implementación concreta debe proporcionar:
    - Un cliente OpenAI asíncrono configurado.
    - El nombre del modelo a usar.
    - El nombre del deployment (si aplica, None en caso contrario).
    """

    @property
    @abstractmethod
    def cliente(self) -> openai.AsyncOpenAI:
        """Cliente OpenAI asíncrono listo para usar."""
        ...

    @property
    @abstractmethod
    def modelo(self) -> str:
        """Nombre del modelo (ej: gpt-5.6-luna)."""
        ...

    @property
    @abstractmethod
    def deployment(self) -> Optional[str]:
        """Nombre del deployment en Azure/Foundry, o None si no aplica."""
        ...


class ProveedorEmbeddings(ABC):
    """Contrato abstracto para proveedores de embeddings.

    Cualquier implementación concreta debe proporcionar:
    - Un cliente OpenAI asíncrono configurado.
    - El nombre del modelo de embeddings.
    - El nombre del deployment (si aplica).
    - Las dimensiones del vector de embedding.
    """

    @property
    @abstractmethod
    def cliente(self) -> openai.AsyncOpenAI:
        """Cliente OpenAI asíncrono listo para usar."""
        ...

    @property
    @abstractmethod
    def modelo(self) -> str:
        """Nombre del modelo de embeddings (ej: text-embedding-3-large)."""
        ...

    @property
    @abstractmethod
    def deployment(self) -> Optional[str]:
        """Nombre del deployment en Azure/Foundry, o None si no aplica."""
        ...

    @property
    @abstractmethod
    def dimensiones(self) -> Optional[int]:
        """Dimensiones del vector (None si el modelo no soporta dimensions)."""
        ...


# =============================================================================
# IMPLEMENTACIONES — USO DIRECTO DESDE openai_clients.py
# =============================================================================


class ProveedorLLMBase(ProveedorLLM):
    """Implementación base de ProveedorLLM.

    Recibe cliente, modelo y deployment ya resueltos desde configuración.
    La creación del cliente se delega a ``openai_clients.py``.
    """

    def __init__(
        self,
        cliente: openai.AsyncOpenAI,
        modelo: str,
        deployment: Optional[str] = None,
    ) -> None:
        self._cliente = cliente
        self._modelo = modelo
        self._deployment = deployment

    @property
    def cliente(self) -> openai.AsyncOpenAI:
        return self._cliente

    @property
    def modelo(self) -> str:
        return self._modelo

    @property
    def deployment(self) -> Optional[str]:
        return self._deployment


class ProveedorEmbeddingsBase(ProveedorEmbeddings):
    """Implementación base de ProveedorEmbeddings.

    Recibe cliente, modelo, deployment y dimensiones ya resueltos desde
    configuración. La creación del cliente se delega a ``openai_clients.py``.
    """

    def __init__(
        self,
        cliente: openai.AsyncOpenAI,
        modelo: str,
        deployment: Optional[str] = None,
        dimensiones: Optional[int] = None,
    ) -> None:
        self._cliente = cliente
        self._modelo = modelo
        self._deployment = deployment
        self._dimensiones = dimensiones

    @property
    def cliente(self) -> openai.AsyncOpenAI:
        return self._cliente

    @property
    def modelo(self) -> str:
        return self._modelo

    @property
    def deployment(self) -> Optional[str]:
        return self._deployment

    @property
    def dimensiones(self) -> Optional[int]:
        return self._dimensiones


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def crear_proveedor_llm(
    cliente: openai.AsyncOpenAI,
    modelo: str,
    deployment: Optional[str] = None,
) -> ProveedorLLM:
    """Crea un ProveedorLLM a partir de parámetros ya resueltos.

    Args:
        cliente: Cliente OpenAI asíncrono ya configurado.
        modelo: Nombre del modelo LLM.
        deployment: Nombre del deployment (Azure/Foundry) o None.

    Returns:
        ProveedorLLM listo para usar.
    """
    return ProveedorLLMBase(cliente=cliente, modelo=modelo, deployment=deployment)


def crear_proveedor_embeddings(
    cliente: openai.AsyncOpenAI,
    modelo: str,
    deployment: Optional[str] = None,
    dimensiones: Optional[int] = None,
) -> ProveedorEmbeddings:
    """Crea un ProveedorEmbeddings a partir de parámetros ya resueltos.

    Args:
        cliente: Cliente OpenAI asíncrono ya configurado.
        modelo: Nombre del modelo de embeddings.
        deployment: Nombre del deployment (Azure/Foundry) o None.
        dimensiones: Dimensiones del vector (None si el modelo no las soporta).

    Returns:
        ProveedorEmbeddings listo para usar.
    """
    return ProveedorEmbeddingsBase(
        cliente=cliente,
        modelo=modelo,
        deployment=deployment,
        dimensiones=dimensiones,
    )