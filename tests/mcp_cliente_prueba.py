"""
Cliente MCP de prueba — Prueba End-to-End del RAG Institucional.

Propósito:
    Demuestra el flujo completo:
    AGENTE -> MCP -> RAG -> PostgreSQL -> MCP -> AGENTE

    Ejecuta las 3 herramientas MCP secuencialmente:
    1. cargar_contenido_rag (ingesta desde facultadesUR2026.md)
    2. consultar_rag_institucional (consulta semántica)
    3. obtener_documento_rag (recuperación del documento)

Uso:
    python tests/mcp_cliente_prueba.py          # Modo real (requiere BD)
    python tests/mcp_cliente_prueba.py --mock    # Modo simulado

Prerrequisitos (modo real):
    - PostgreSQL con pgvector habilitado
    - BD rag_institucional creada
    - Variables de entorno configuradas
    - Azure AI Foundry o mock de embeddings

Estructura:
    PRUEBA A: cargar_contenido_rag con facultadesUR2026.md
    PRUEBA B: consultar_rag_institucional
    PRUEBA C: Validación de resultados (fuente, score, documento_id)
    PRUEBA D: obtener_documento_rag con documento_id
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp_cliente_prueba")

resultados: list[dict] = []
PASSED, FAILED, SKIPPED = "PASSED", "FAILED", "SKIPPED"


def registrar(nombre: str, estado: str, detalle: str = ""):
    resultados.append({"nombre": nombre, "estado": estado, "detalle": detalle})
    icono = {"PASSED": "✅", "FAILED": "❌", "SKIPPED": "⏭️"}.get(estado, "❓")
    logger.info("%s %s: %s", icono, nombre, detalle)


async def prueba_completa(mock_mode: bool = False) -> bool:
    """Ejecuta el flujo E2E completo."""
    logger.info("=" * 60)
    logger.info("PRUEBA E2E - RAG Institucional UR")
    logger.info("=" * 60)

    if mock_mode:
        logger.info("Modo MOCK: simulación sin BD real.")
        for p in ["A-Carga", "B-Consulta", "C-Validacion", "D-Obtencion"]:
            registrar(f"PRUEBA {p} (mock)", SKIPPED, "Requiere modo real.")
        logger.info("Usar: python tests/mcp_cliente_prueba.py (sin --mock)")
        return True

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        from dotenv import load_dotenv
        load_dotenv(override=True)

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "fastapi_app.mcp_servidor_main"],
        )

        logger.info("Conectando MCP Server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.info("MCP Server conectado.")

                # PRUEBA A: Cargar contenido
                ruta = os.path.join(os.path.dirname(__file__), "facultadesUR2026.md")
                if not os.path.exists(ruta):
                    registrar("PRUEBA A - Carga", FAILED, f"Archivo no encontrado: {ruta}")
                    return False

                with open(ruta, "r", encoding="utf-8") as f:
                    contenido = f.read()

                logger.info("PRUEBA A: Cargando...")
                res = await session.call_tool("cargar_contenido_rag", arguments={
                    "titulo": "Facultades de la Universidad del Rosario",
                    "contenido": contenido,
                    "fuente": "https://www.urosario.edu.co/universidad/facultades/",
                    "tipo_documento": "facultad",
                })
                datos = _extraer_dict(res)
                if datos.get("documento_id", 0) > 0:
                    registrar("PRUEBA A - Carga", PASSED,
                              f"Doc {datos['documento_id']}: {datos['cantidad_fragmentos']} fragmentos.")
                else:
                    registrar("PRUEBA A - Carga", FAILED, str(datos))
                    return False

                doc_id = datos["documento_id"]

                # PRUEBA B: Consultar
                logger.info("PRUEBA B: Consultando...")
                res2 = await session.call_tool("consultar_rag_institucional", arguments={
                    "consulta": "¿Cuales son las facultades de la Universidad del Rosario?",
                    "limite": 5,
                })
                datos2 = _extraer_lista(res2)
                registrar("PRUEBA B - Consulta", PASSED if datos2 else FAILED,
                          f"{len(datos2)} resultados.")

                # PRUEBA C: Validacion
                logger.info("PRUEBA C: Validando...")
                if datos2:
                    p = datos2[0]
                    ok = all([p.get("contenido"), p.get("documento_id") == doc_id,
                              p.get("fuente"), isinstance(p.get("score"), (int, float))])
                    registrar("PRUEBA C - Validacion", PASSED if ok else FAILED,
                              f"doc_id={p['documento_id']} score={p.get('score', 'N/A')}")
                else:
                    registrar("PRUEBA C - Validacion", SKIPPED, "Sin datos.")

                # PRUEBA D: Obtener documento
                logger.info("PRUEBA D: Obteniendo doc %d...", doc_id)
                res3 = await session.call_tool("obtener_documento_rag", arguments={"documento_id": doc_id})
                datos3 = _extraer_dict(res3)
                ok = datos3.get("documento_id") == doc_id
                registrar("PRUEBA D - Obtencion", PASSED if ok else FAILED,
                          f"'{datos3.get('titulo', '?')}' - {datos3.get('cantidad_fragmentos', 0)} fragmentos.")

    except ImportError as e:
        registrar("PRUEBA E2E", FAILED, f"Import Error: {e}")
    except Exception as e:
        registrar("PRUEBA E2E", FAILED, f"Error: {e}")
        logger.exception("Detalle:")

    # Resumen
    total = len(resultados)
    passed = sum(1 for r in resultados if r["estado"] == PASSED)
    failed = sum(1 for r in resultados if r["estado"] == FAILED)
    logger.info("=" * 60)
    logger.info(f"Total: {total} | PASSED: {passed} | FAILED: {failed}")
    return failed == 0


def _extraer_dict(r) -> dict:
    try:
        t = r.content[0].text
        return json.loads(t)
    except (AttributeError, IndexError, json.JSONDecodeError):
        return {}


def _extraer_lista(r) -> list:
    try:
        t = r.content[0].text
        return json.loads(t)
    except (AttributeError, IndexError, json.JSONDecodeError):
        return []


async def main():
    mock_mode = "--mock" in sys.argv
    ok = await prueba_completa(mock_mode=mock_mode)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())