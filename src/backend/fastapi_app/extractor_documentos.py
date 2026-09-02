"""
Extractor de documentos multiformato para el RAG Institucional.

Propósito:
    Proporciona una abstracción unificada para extraer contenido textual
    de documentos en diferentes formatos (Markdown, PDF, TXT, futuros DOCX).
    Implementa el patrón Strategy para seleccionar el extractor adecuado
    según el formato del archivo.

Contexto arquitectónico:
    El RAG Institucional recibe documentos en múltiples formatos. Cada
    extractor concreto implementa la interfaz ``ExtractorDocumento`` y
    devuelve un ``ResultadoExtraccion`` normalizado con el contenido
    textual y metadatos del documento.

Formatos soportados actualmente:
    - **Markdown (.md)**: Extracción directa del texto UTF-8.
    - **PDF (.pdf)**: Extracción página por página usando PyMuPDF.
    - **TXT (.txt)**: Extracción directa del texto UTF-8.

Seguridad:
    - Los extractores no ejecutan código incrustado en los documentos.
    - Los nombres de archivo se limpian de path traversal.
    - Los PDF malformados se detectan y reportan sin crash.
    - Tamaños de archivo excesivos se rechazan antes de extraer.

Dependencias:
    - PyMuPDF (pymupdf): para extracción de PDFs.
    - No requiere librerías adicionales para MD/TXT.
"""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ragapp")

# =============================================================================
# CONSTANTES
# =============================================================================

EXTENSIONES_PDF: set[str] = {".pdf"}
EXTENSIONES_MD: set[str] = {".md", ".markdown"}
EXTENSIONES_TXT: set[str] = {".txt", ".text"}
FORMATOS_SOPORTADOS: set[str] = EXTENSIONES_PDF | EXTENSIONES_MD | EXTENSIONES_TXT
TAMANO_MAXIMO_BYTES: int = 100 * 1024 * 1024  # 100MB
# =============================================================================
# RESULTADO DE EXTRACCIÓN
# =============================================================================


@dataclass
class ResultadoExtraccion:
    """Resultado normalizado de la extracción de un documento."""
    contenido: str
    cantidad_caracteres: int
    cantidad_paginas: Optional[int] = None
    cantidad_fragmentos_sugeridos: int = 0
    metadatos: dict = field(default_factory=dict)
    hash_sha256: Optional[str] = None
    tamano_bytes: int = 0
    nombre_archivo_original: str = ""
    exito: bool = True
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.cantidad_caracteres == 0 and self.contenido:
            self.cantidad_caracteres = len(self.contenido)


# =============================================================================
# INTERFAZ EXTRACTOR
# =============================================================================


class ExtractorDocumento(ABC):
    """Contrato abstracto para extractores de documentos."""

    @abstractmethod
    def extraer(self, ruta_archivo: str) -> ResultadoExtraccion:
        """Extrae el contenido textual de un documento."""
        ...

    def _validar_archivo(self, ruta_archivo: str) -> int:
        """Valida que el archivo exista y no exceda el tamaño máximo."""
        path = Path(ruta_archivo)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")
        if not path.is_file():
            raise ValueError(f"No es un archivo válido: {ruta_archivo}")
        tamano = path.stat().st_size
        if tamano > TAMANO_MAXIMO_BYTES:
            raise ValueError(
                f"Archivo demasiado grande: {tamano:,} bytes. "
                f"Límite: {TAMANO_MAXIMO_BYTES:,} bytes."
            )
        return tamano

    def _calcular_hash(self, contenido: str) -> str:
        """Calcula el hash SHA-256 del contenido extraído."""
        return hashlib.sha256(contenido.encode("utf-8")).hexdigest()
# =============================================================================
# EXTRACTOR MARKDOWN
# =============================================================================


class ExtractorMarkdown(ExtractorDocumento):
    """Extractor para documentos Markdown (.md, .markdown)."""

    def extraer(self, ruta_archivo: str) -> ResultadoExtraccion:
        """Extrae contenido de un archivo Markdown."""
        tamano = self._validar_archivo(ruta_archivo)
        nombre_archivo = Path(ruta_archivo).name

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                contenido = f.read()
        except UnicodeDecodeError:
            with open(ruta_archivo, "r", encoding="latin-1") as f:
                contenido = f.read()

        contenido = contenido.strip()
        if not contenido:
            return ResultadoExtraccion(
                contenido="", cantidad_caracteres=0, tamano_bytes=tamano,
                nombre_archivo_original=nombre_archivo, exito=False,
                error="El archivo Markdown está vacío.",
            )

        metadatos = self._extraer_metadatos_markdown(contenido)

        return ResultadoExtraccion(
            contenido=contenido, cantidad_caracteres=len(contenido),
            cantidad_paginas=None,
            cantidad_fragmentos_sugeridos=self._estimar_fragmentos(contenido),
            metadatos=metadatos, hash_sha256=self._calcular_hash(contenido),
            tamano_bytes=tamano, nombre_archivo_original=nombre_archivo, exito=True,
        )

    def _extraer_metadatos_markdown(self, contenido: str) -> dict:
        """Extrae metadatos básicos del contenido Markdown."""
        metadatos: dict = {}
        for linea in contenido.split("\n")[:20]:
            s = linea.strip()
            if "titulo" not in metadatos and s.startswith("#"):
                titulo = s.lstrip("#").strip()
                if titulo:
                    metadatos["titulo"] = titulo
            if "fuente" not in metadatos and "**Fuente:**" in s:
                metadatos["fuente"] = s.replace("**Fuente:**", "").strip().strip(">").strip()
            if "url" not in metadatos and "**URL:**" in s:
                metadatos["url"] = s.replace("**URL:**", "").strip().strip(">").strip()
        return metadatos

    def _estimar_fragmentos(self, contenido: str) -> int:
        """Estima fragmentos contando encabezados Markdown."""
        encabezados = len(re.findall(r"^##\s", contenido, re.MULTILINE))
        return max(1, encabezados)


# =============================================================================
# EXTRACTOR PDF
# =============================================================================


class ExtractorPDF(ExtractorDocumento):
    """Extractor para documentos PDF (.pdf) usando PyMuPDF."""

    def extraer(self, ruta_archivo: str) -> ResultadoExtraccion:
        """Extrae contenido de un archivo PDF página por página."""
        tamano = self._validar_archivo(ruta_archivo)
        nombre_archivo = Path(ruta_archivo).name

        try:
            import pymupdf
        except ImportError:
            return ResultadoExtraccion(
                contenido="", cantidad_caracteres=0, tamano_bytes=tamano,
                nombre_archivo_original=nombre_archivo, exito=False,
                error="PyMuPDF no está instalado. Ejecute: pip install pymupdf",
            )

        try:
            doc = pymupdf.open(ruta_archivo)
        except Exception as e:
            return ResultadoExtraccion(
                contenido="", cantidad_caracteres=0, tamano_bytes=tamano,
                nombre_archivo_original=nombre_archivo, exito=False,
                error=f"Error al abrir PDF: {e}",
            )

        try:
            cantidad_paginas = doc.page_count
            contenido_paginas: list[str] = []
            metadatos: dict = {}
            total_caracteres = 0

            pdf_metadata = doc.metadata
            if pdf_metadata:
                for campo in ("title", "author", "subject", "keywords"):
                    valor = pdf_metadata.get(campo)
                    if valor:
                        metadatos[campo] = valor

            for num_pagina in range(cantidad_paginas):
                pagina = doc.load_page(num_pagina)
                texto = pagina.get_text().strip()
                if texto:
                    contenido_paginas.append(texto)
                    total_caracteres += len(texto)

            contenido = "\n\n".join(contenido_paginas)

            if not contenido:
                return ResultadoExtraccion(
                    contenido="", cantidad_caracteres=0,
                    cantidad_paginas=cantidad_paginas, tamano_bytes=tamano,
                    nombre_archivo_original=nombre_archivo, exito=False,
                    error=f"PDF escaneado sin texto extraíble ({cantidad_paginas} págs). "
                          "OCR no disponible.",
                )

            return ResultadoExtraccion(
                contenido=contenido, cantidad_caracteres=total_caracteres,
                cantidad_paginas=cantidad_paginas,
                cantidad_fragmentos_sugeridos=cantidad_paginas,
                metadatos=metadatos, hash_sha256=self._calcular_hash(contenido),
                tamano_bytes=tamano, nombre_archivo_original=nombre_archivo, exito=True,
            )

        except Exception as e:
            logger.error("Error extrayendo PDF %s: %s", nombre_archivo, e)
            return ResultadoExtraccion(
                contenido="", cantidad_caracteres=0, tamano_bytes=tamano,
                nombre_archivo_original=nombre_archivo, exito=False,
                error=f"Error durante extracción de PDF: {e}",
            )
        finally:
            if "doc" in locals():
                doc.close()


# =============================================================================
# EXTRACTOR TEXTO PLANO
# =============================================================================


class ExtractorTextoPlano(ExtractorDocumento):
    """Extractor para documentos de texto plano (.txt, .text)."""

    def extraer(self, ruta_archivo: str) -> ResultadoExtraccion:
        """Extrae contenido de un archivo de texto plano."""
        tamano = self._validar_archivo(ruta_archivo)
        nombre_archivo = Path(ruta_archivo).name

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                contenido = f.read()
        except UnicodeDecodeError:
            with open(ruta_archivo, "r", encoding="latin-1") as f:
                contenido = f.read()

        contenido = contenido.strip()
        if not contenido:
            return ResultadoExtraccion(
                contenido="", cantidad_caracteres=0, tamano_bytes=tamano,
                nombre_archivo_original=nombre_archivo, exito=False,
                error="El archivo de texto está vacío.",
            )

        return ResultadoExtraccion(
            contenido=contenido, cantidad_caracteres=len(contenido),
            cantidad_paginas=None, cantidad_fragmentos_sugeridos=1,
            metadatos={}, hash_sha256=self._calcular_hash(contenido),
            tamano_bytes=tamano, nombre_archivo_original=nombre_archivo, exito=True,
        )


# =============================================================================
# REGISTRO DE EXTRACTORES
# =============================================================================

EXTRACTORS: dict[str, ExtractorDocumento] = {
    "pdf": ExtractorPDF(),
    "md": ExtractorMarkdown(),
    "txt": ExtractorTextoPlano(),
}


def obtener_extractor(extension: str) -> Optional[ExtractorDocumento]:
    """Obtiene el extractor adecuado para una extensión de archivo."""
    return EXTRACTORS.get(extension.lower().lstrip("."))


def extraer_documento(ruta_archivo: str) -> ResultadoExtraccion:
    """Extrae contenido seleccionando el extractor según el formato del archivo.

    Args:
        ruta_archivo: Ruta absoluta al archivo.

    Returns:
        ResultadoExtraccion normalizado.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el formato no es soportado.
    """
    path = Path(ruta_archivo)
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta_archivo}")

    extension = path.suffix.lower()
    if extension not in FORMATOS_SOPORTADOS:
        raise ValueError(
            f"Formato no soportado: '{extension}'. "
            f"Formatos soportados: {', '.join(sorted(FORMATOS_SOPORTADOS))}"
        )

    extractor = obtener_extractor(extension)
    if extractor is None:
        raise ValueError(f"No hay extractor registrado para: '{extension}'")

    return extractor.extraer(ruta_archivo)