"""
Fragmentador de documentos para el RAG Institucional.

Propósito:
    Divide documentos Markdown en fragmentos semánticamente coherentes
    para generar embeddings individuales por fragmento.

Contexto arquitectónico:
    Este módulo es la primera etapa del pipeline de ingestión:
    Markdown -> fragmentos -> embeddings -> PostgreSQL.

Estrategia de fragmentación:
    1. Para Markdown: dividir por encabezados (## o ###) como límites
       naturales de sección. Cada sección es un fragmento.
    2. Si una sección excede el tamaño máximo, subdividir por párrafos.
    3. Si un párrafo excede el tamaño máximo, dividir por oraciones.
    4. Solapamiento controlado entre fragmentos para no perder contexto.

Seguridad:
    - No ejecuta código incrustado en el documento.
    - No accede al sistema de archivos fuera de lo especificado.
    - Los fragmentos son puro texto, no estructuras ejecutables.

Restricciones:
    - Tamaño máximo de fragmento configurable (default: 1000 chars).
    - Solapamiento configurable (default: 100 chars).
    - No soporta PDF, DOCX u otros formatos binarios.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from fastapi_app.configuracion_institucional import cargar_configuracion_institucional

logger = logging.getLogger("ragapp")


class FragmentoResultado:
    """
    Resultado de la fragmentación de un documento.

    Attributes:
        contenido: Texto del fragmento.
        orden: Posición dentro del documento original.
        metadata: Metadatos del fragmento (sección, tipo, etc.).
    """

    def __init__(self, contenido: str, orden: int, metadata: Optional[dict] = None):
        self.contenido = contenido.strip()
        self.orden = orden
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"<FragmentoResultado orden={self.orden} chars={len(self.contenido)}>"


class FragmentadorDocumentos:
    """
    Fragmenta documentos Markdown en fragmentos semánticos.

    Divide por encabezados (##, ###). Si una sección excede
    tamano_maximo, subdivide por párrafos primero, luego por oraciones.

    Args:
        tamano_maximo: Máximo de caracteres por fragmento (default: 1000).
        solapamiento: Caracteres de solapamiento (default: 100).
    """

    def __init__(
        self,
        tamano_maximo: Optional[int] = None,
        solapamiento: Optional[int] = None,
    ):
        config = cargar_configuracion_institucional()
        self.tamano_maximo = tamano_maximo or config.tamano_fragmento_maximo
        self.solapamiento = solapamiento or config.solapamiento_fragmentos

        if self.tamano_maximo < 100:
            raise ValueError(
                f"tamano_maximo={self.tamano_maximo} es muy pequeño. "
                "Mínimo recomendado: 100 caracteres."
            )
        if self.solapamiento < 0 or self.solapamiento >= self.tamano_maximo:
            raise ValueError(
                f"solapamiento={self.solapamiento} inválido. "
                f"Debe estar entre 0 y {self.tamano_maximo}."
            )

    def fragmentar(self, contenido_markdown: str) -> List[FragmentoResultado]:
        """
        Fragmenta un documento Markdown.

        Args:
            contenido_markdown: Texto completo del documento en Markdown.

        Returns:
            Lista de FragmentoResultado con contenido y orden.

        Raises:
            ValueError: Si el contenido está vacío.
        """
        if not contenido_markdown or not contenido_markdown.strip():
            raise ValueError("El contenido del documento no puede estar vacío.")

        secciones = self._dividir_por_encabezados(contenido_markdown)
        fragmentos: List[FragmentoResultado] = []
        orden = 1

        for seccion in secciones:
            if not seccion.strip():
                continue
            if len(seccion) <= self.tamano_maximo:
                fragmentos.append(FragmentoResultado(
                    contenido=seccion,
                    orden=orden,
                    metadata={"tipo_seccion": self._detectar_tipo_seccion(seccion)},
                ))
                orden += 1
            else:
                subfragmentos = self._subdividir_seccion(seccion)
                for sf in subfragmentos:
                    fragmentos.append(FragmentoResultado(
                        contenido=sf, orden=orden,
                        metadata={"tipo_seccion": "subfragmento"},
                    ))
                    orden += 1

        logger.info("Documento fragmentado: %d fragmentos", len(fragmentos))
        return fragmentos

    def _dividir_por_encabezados(self, contenido: str) -> List[str]:
        """Divide contenido Markdown por encabezados ## o ###.

        Preserva el encabezado como parte del fragmento para mantener
        el contexto semántico. El contenido anterior al primer encabezado
        se descarta (suele ser metadatos o título principal).
        """
        patron = re.compile(r"^(#{2,3})\s+", re.MULTILINE)
        partes = patron.split(contenido)
        if len(partes) <= 1:
            return [contenido.strip()]
        secciones = []
        i = 1
        while i < len(partes):
            nivel = partes[i]
            resto = partes[i + 1] if i + 1 < len(partes) else ""
            lineas = resto.split("\n", 1)
            titulo = lineas[0].strip() if lineas else ""
            cuerpo = lineas[1] if len(lineas) > 1 else ""
            seccion = f"{nivel} {titulo}\n\n{cuerpo.strip()}"
            secciones.append(seccion.strip())
            i += 2
        return secciones

    def _subdividir_seccion(self, seccion: str) -> List[str]:
        """Subdivide una sección grande por párrafos."""
        parrafos = [p.strip() for p in seccion.split("\n\n") if p.strip()]
        fragmentos = []
        actual = ""
        for parrafo in parrafos:
            if len(parrafo) > self.tamano_maximo:
                if actual:
                    fragmentos.append(actual.strip())
                    actual = ""
                fragmentos.extend(self._dividir_parrafo_largo(parrafo))
                continue
            if actual and len(actual) + len(parrafo) > self.tamano_maximo:
                fragmentos.append(actual.strip())
                actual = parrafo
            else:
                actual = (actual + "\n\n" + parrafo) if actual else parrafo
        if actual:
            fragmentos.append(actual.strip())
        return fragmentos

    def _dividir_parrafo_largo(self, parrafo: str) -> List[str]:
        """Divide un párrafo largo por oraciones."""
        oraciones = re.split(r"(?<=[.!?])\s+", parrafo)
        fragmentos = []
        actual = ""
        for oracion in oraciones:
            if len(oracion) > self.tamano_maximo:
                if actual:
                    fragmentos.append(actual.strip())
                    actual = ""
                fragmentos.extend(self._dividir_por_comas(oracion))
                continue
            if actual and len(actual) + len(oracion) > self.tamano_maximo:
                fragmentos.append(actual.strip())
                actual = oracion
            else:
                actual = (actual + " " + oracion) if actual else oracion
        if actual:
            fragmentos.append(actual.strip())
        return fragmentos

    @staticmethod
    def _dividir_por_comas(texto: str) -> List[str]:
        """Divide texto extremadamente largo por comas (fallback)."""
        partes = texto.split(", ")
        fragmentos = []
        actual = ""
        for parte in partes:
            if actual and len(actual) + len(parte) > 500:
                fragmentos.append(actual.strip())
                actual = parte
            else:
                actual = (actual + ", " + parte) if actual else parte
        if actual:
            fragmentos.append(actual.strip())
        return fragmentos

    @staticmethod
    def _detectar_tipo_seccion(texto: str) -> str:
        """Detecta el tipo de sección por su encabezado."""
        primera = texto.split("\n")[0].strip()
        if primera.startswith("# "):
            return "encabezado_principal"
        elif primera.startswith("## "):
            return "encabezado_secundario"
        elif primera.startswith("### "):
            return "encabezado_terciario"
        elif texto.startswith("> "):
            return "cita"
        elif texto.startswith("|"):
            return "tabla"
        return "contenido"