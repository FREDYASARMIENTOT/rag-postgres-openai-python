"""
Servicio de generacion RAG para el RAG Institucional.

Proposito:
    Orquesta el flujo completo: consulta -> retrieval -> contexto -> LLM -> respuesta.

Contexto arquitectonico:
    Conecta ServicioRetrieval con un LLM (GPT-5.6 Luna) para generar respuestas
    fundamentadas en los fragmentos recuperados de PostgreSQL + pgvector.

    Pipeline:
        1. Recibir consulta
        2. Generar embedding (delegado a ServicioRetrieval)
        3. Recuperar fragmentos relevantes (delegado a ServicioRetrieval)
        4. Construir contexto con fragmentos
        5. Llamar a Foundry (GPT-5.6 Luna) con el contexto
        6. Devolver respuesta fundamentada

Seguridad:
    - No expone embeddings internos.
    - No permite SQL injection.
    - El prompt del sistema instruye al modelo a no inventar informacion.
    - Si no hay contexto suficiente, el modelo debe indicarlo.

Dependencias:
    - ServicioRetrieval (para retrieval)
    - ProveedorLLM (para chat)
    - openai.AsyncOpenAI (llamada real a Foundry)
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from fastapi_app.proveedores import ProveedorLLM
from fastapi_app.servicio_retrieval import ServicioRetrieval

logger = logging.getLogger("ragapp")


# =============================================================================
# CONSTANTES DEL PROMPT DE SISTEMA
# =============================================================================

SYSTEM_PROMPT_RAG_INSTITUCIONAL = (
    "Eres un asistente experto en la Universidad del Rosario. "
    "Tu funcion es responder preguntas sobre la universidad utilizando "
    "exclusivamente la informacion proporcionada en el contexto siguiente. "
    "Debes seguir estas reglas:\n"
    "1. Responde SOLO con informacion que este explicitamente en el contexto.\n"
    "2. NO inventes facultades, decanos, programas, fechas o datos.\n"
    "3. Si la informacion no esta en el contexto, indica claramente que "
    "no tienes esa informacion disponible.\n"
    "4. Responde en espanol, de forma clara y profesional.\n"
    "5. Cita la fuente del documento cuando sea relevante.\n"
    "6. Si el contexto contiene informacion parcial, indica lo que sabes "
    "y lo que no puedes responder por falta de informacion.\n\n"
    "Contexto:\n"
    "---\n"
    "{contexto}\n"
    "---"
)
"""Prompt de sistema para el RAG Institucional.

Args:
    contexto: Fragmentos recuperados de la busqueda semantica.
"""


# =============================================================================
# GENERACION RAG
# =============================================================================


class ResultadoGeneracion:
    """Resultado de una consulta RAG con generacion.

    Attributes:
        consulta: Pregunta original.
        respuesta: Texto generado por el LLM.
        fragmentos: Lista de fragmentos recuperados con sus scores.
        deployment: Deployment del LLM utilizado.
        modelo: Nombre del modelo LLM.
        fragmentos_count: Cantidad de fragmentos usados como contexto.
    """

    def __init__(
        self,
        consulta: str,
        respuesta: str,
        fragmentos: list[dict],
        deployment: str,
        modelo: str,
    ) -> None:
        self.consulta = consulta
        self.respuesta = respuesta
        self.fragmentos = fragmentos
        self.deployment = deployment
        self.modelo = modelo
        self.fragmentos_count = len(fragmentos)

    def to_dict(self) -> dict:
        return {
            "consulta": self.consulta,
            "respuesta": self.respuesta,
            "fragmentos_count": self.fragmentos_count,
            "deployment": self.deployment,
            "modelo": self.modelo,
            "fragmentos": [
                {
                    "contenido": f["contenido"][:200] + "..." if len(f["contenido"]) > 200 else f["contenido"],
                    "score": f["score"],
                    "titulo": f["titulo"],
                    "fuente": f["fuente"],
                }
                for f in self.fragmentos
            ],
        }

    def __repr__(self) -> str:
        return (
            f"<ResultadoGeneracion consulta='{self.consulta[:50]}' "
            f"deployment={self.deployment} fragmentos={self.fragmentos_count}>"
        )


class ServicioGeneracion:
    """Servicio de generacion RAG.

    Orquesta el flujo completo de consulta RAG con generacion de respuestas
    utilizando un LLM (GPT-5.6 Luna) fundamentado en los fragmentos recuperados.

    Args:
        servicio_retrieval: Servicio de busqueda semantica.
        proveedor_llm: Proveedor de LLM (chat).
    """

    def __init__(
        self,
        servicio_retrieval: ServicioRetrieval,
        proveedor_llm: ProveedorLLM,
    ) -> None:
        self.servicio_retrieval = servicio_retrieval
        self.proveedor_llm = proveedor_llm

    async def consultar_con_generacion(
        self,
        consulta: str,
        limite: int = 5,
    ) -> ResultadoGeneracion:
        """Ejecuta consulta RAG completa: retrieval + generacion.

        Args:
            consulta: Pregunta en lenguaje natural.
            limite: Maximo de fragmentos a recuperar (default: 5).

        Returns:
            ResultadoGeneracion con respuesta y trazabilidad.

        Raises:
            ValueError: Consulta vacia.
            RuntimeError: Sin proveedor LLM configurado.
        """
        if not consulta or not consulta.strip():
            raise ValueError("La consulta no puede estar vacia.")

        logger.info(
            "Generacion RAG: consulta='%s' limite=%d deployment=%s",
            consulta[:100], limite, self.proveedor_llm.deployment,
        )

        # Paso 1: Retrieval semantico
        resultados = await self.servicio_retrieval.consultar(
            consulta=consulta, limite=limite,
        )

        if not resultados:
            logger.warning("Generacion RAG: sin fragmentos recuperados para '%s'", consulta[:100])
            respuesta = (
                "No se encontraron documentos relevantes en la base de conocimiento "
                "institucional para responder a su consulta."
            )
            return ResultadoGeneracion(
                consulta=consulta,
                respuesta=respuesta,
                fragmentos=[],
                deployment=str(self.proveedor_llm.deployment or ""),
                modelo=self.proveedor_llm.modelo,
            )

        # Paso 2: Construir contexto a partir de fragmentos
        fragmentos_dict = [r.to_dict() for r in resultados]
        contexto = self._construir_contexto(fragmentos_dict)

        # Paso 3: Llamar al LLM
        respuesta = await self._llamar_llm(consulta, contexto)

        return ResultadoGeneracion(
            consulta=consulta,
            respuesta=respuesta,
            fragmentos=fragmentos_dict,
            deployment=str(self.proveedor_llm.deployment or ""),
            modelo=self.proveedor_llm.modelo,
        )

    @staticmethod
    def _construir_contexto(fragmentos: list[dict]) -> str:
        """Construye el contexto a partir de los fragmentos recuperados."""
        partes = []
        for i, frag in enumerate(fragmentos, 1):
            partes.append(
                f"[Fragmento {i}] (Fuente: {frag['fuente']}, "
                f"Documento: {frag['titulo']}, Relevancia: {frag['score']:.4f})\n"
                f"{frag['contenido']}\n"
            )
        return "\n".join(partes)

    async def _llamar_llm(self, consulta: str, contexto: str) -> str:
        """Llama al LLM (Foundry/GPT-5.6 Luna) con prompt del sistema y consulta."""
        cliente: AsyncOpenAI = self.proveedor_llm.cliente
        model_name = self.proveedor_llm.deployment or self.proveedor_llm.modelo

        system_prompt = SYSTEM_PROMPT_RAG_INSTITUCIONAL.format(contexto=contexto)

        logger.info(
            "Llamando a LLM: model=%s deployment=%s contexto_len=%d",
            self.proveedor_llm.modelo, model_name, len(contexto),
        )

        try:
            response = await cliente.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": consulta},
                ],
                temperature=1.0,
                max_completion_tokens=2048,
            )

            mensaje = response.choices[0].message
            if mensaje.content is None:
                logger.warning("LLM returned empty response")
                return "El modelo no genero una respuesta."

            logger.info(
                "LLM respondio: %d tokens, stop_reason=%s",
                len(mensaje.content),
                response.choices[0].finish_reason,
            )
            return mensaje.content

        except Exception as e:
            logger.error("Error al llamar al LLM: %s", e)
            raise

    def to_dict(self) -> dict:
        return {
            "consulta": self.consulta,
            "respuesta": self.respuesta,
            "fragmentos_count": self.fragmentos_count,
            "deployment": self.deployment,
            "modelo": self.modelo,
            "fragmentos": [
                {
                    "contenido": f["contenido"][:200] + "..." if len(f["contenido"]) > 200 else f["contenido"],
                    "score": f["score"],
                    "titulo": f["titulo"],
                    "fuente": f["fuente"],
                }
                for f in self.fragmentos
            ],
        }

    def __repr__(self) -> str:
        return (
            f"<ResultadoGeneracion consulta='{self.consulta[:50]}' "
            f"deployment={self.deployment} fragmentos={self.fragmentos_count}>"
        )