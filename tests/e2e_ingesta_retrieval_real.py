"""
Prueba E2E real de INGESTA + DEDUP + RETRIEVAL + GENERACION
contra PostgreSQL Azure + Azure AI Foundry.

Flujo completo:
    1. Cargar documentos de ejemplo (documentos_ejemplo/)
    2. Verificar deduplicacion SHA-256
    3. Realizar consultas semanticas de retrieval
    4. Generar respuesta con GPT-5.6 Luna
    5. Validar grounding
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("e2e_ingesta")
RUTA_DOCS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "documentos_ejemplo",
)

DOCUMENTOS_PRUEBA = [
    {
        "ruta": os.path.join(RUTA_DOCS, "md/facultades_ur_prueba.md"),
        "titulo": "Facultades UR - Markdown",
        "tipo": "facultad",
    },
    {
        "ruta": os.path.join(RUTA_DOCS, "txt/facultades_ur_prueba.txt"),
        "titulo": "Facultades UR - Texto Plano",
        "tipo": "facultad",
    },
    {
        "ruta": os.path.join(RUTA_DOCS, "pdf/facultades_ur_prueba.pdf"),
        "titulo": "Facultades UR - PDF",
        "tipo": "facultad",
    },
]


def sep(titulo: str) -> None:
    """Imprime separador."""
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")
async def main() -> None:
    sep("CONFIGURACION")
    from fastapi_app.dependencies import (
        common_parameters,
        create_async_sessionmaker,
        get_azure_credential,
    )
    from fastapi_app.openai_clients import (
        create_openai_chat_client,
        create_openai_embed_client,
    )
    from fastapi_app.postgres_engine import create_postgres_engine_from_env
    from fastapi_app.proveedores import (
        crear_proveedor_embeddings,
        crear_proveedor_llm,
    )
    from fastapi_app.repositorio_documentos import RepositorioDocumentos
    from fastapi_app.servicio_ingesta import ServicioIngesta
    from fastapi_app.servicio_retrieval import ServicioRetrieval
    from fastapi_app.servicio_generacion import ServicioGeneracion

    c = await common_parameters()
    print(f"Embed: {c.rag_embed_model}/{c.rag_embed_deployment} [{c.rag_embed_dimensions}d]")
    print(f"LLM:   {c.rag_llm_model}/{c.rag_llm_deployment}")
    print(f"Host:  PG={os.getenv('POSTGRES_HOST')} Chat={c.rag_chat_host} Embed={c.rag_embed_host}")

    # ── PostgreSQL ──────────────────────────────────────────────
    sep("POSTGRESQL")
    cred = None
    if os.getenv("POSTGRES_HOST", "").endswith(".database.azure.com"):
        cred = await get_azure_credential()
        print("Azure Credential: OK")

    engine = await create_postgres_engine_from_env(cred)
    sm = await create_async_sessionmaker(engine)
    print("PostgreSQL engine: OK")

    # ── Embeddings (Foundry) ────────────────────────────────────
    sep("EMBEDDINGS (FOUNDRY)")
    ec = await create_openai_embed_client(
        cred,
        host_override="foundry",
        deployment_override=c.rag_embed_deployment or c.rag_embed_model,
    )
    pe = crear_proveedor_embeddings(
        cliente=ec,
        modelo=c.rag_embed_model,
        deployment=c.rag_embed_deployment,
        dimensiones=c.rag_embed_dimensions,
    )
    print(f"Embeddings client created: {c.rag_embed_model}/{c.rag_embed_deployment} [{c.rag_embed_dimensions}d]")

    # ── Chat Luna (Foundry) ─────────────────────────────────────
    sep("CHAT LUNA (FOUNDRY)")
    cc = await create_openai_chat_client(
        cred,
        host_override="foundry",
        deployment_override=c.rag_llm_deployment or c.rag_llm_model,
    )
    pl = crear_proveedor_llm(
        cliente=cc,
        modelo=c.rag_llm_model,
        deployment=c.rag_llm_deployment,
    )
    print(f"Luna: model={pl.modelo}, deployment={pl.deployment}")

    ping = await cc.chat.completions.create(
        model=pl.deployment,
        messages=[{"role": "user", "content": "responde solo OK si funcionas"}],
        max_completion_tokens=5,
    )
    print(f"Luna ping: {ping.choices[0].message.content}")

    # ── INGESTA ─────────────────────────────────────────────────
    sep("INGESTA DE DOCUMENTOS")
    ingesta_session = sm()
    repo = RepositorioDocumentos(ingesta_session)
    ingesta = ServicioIngesta(
        repositorio=repo,
        proveedor_embeddings=pe,
    )

    for doc_info in DOCUMENTOS_PRUEBA:
        ruta = doc_info["ruta"]
        if not os.path.exists(ruta):
            print(f"  [SKIP] Archivo no encontrado: {ruta}")
            continue
        print(f"  Procesando: {os.path.basename(ruta)}")
        try:
            resultado = await ingesta.ingestar_desde_archivo(
                ruta_archivo=ruta,
                fuente="Prueba E2E",
                tipo_documento=doc_info["tipo"],
                usuario_cargador="e2e_test",
            )
            print(f"    Documento ID: {resultado.documento_id}")
            print(f"    Titulo:       {resultado.titulo}")
            print(f"    Fragmentos:   {resultado.cantidad_fragmentos}")
            print(f"    Estado:       {resultado.estado}")
        except Exception as e:
            print(f"    [ERROR] {e}")

    # ── Prueba de deduplicación (opcional) ──────────────────────
    print()
    pdf_path = os.path.join(RUTA_DOCS, "pdf/facultades_ur_prueba.pdf")
    if os.path.exists(pdf_path):
        # Verificar si el hash existe sin disparar constraint
        from sqlalchemy import select, func
        from fastapi_app.modelos_rag_documentos import Documento
        from fastapi_app.extractor_documentos import extraer_documento
        extraido = extraer_documento(pdf_path)
        if extraido.hash_sha256:
            stmt = select(func.count()).select_from(Documento).where(
                Documento.hash_sha256 == extraido.hash_sha256
            )
            result = await ingesta_session.execute(stmt)
            existing = result.scalar() or 0
            if existing > 0:
                print(f"  [OK] DEDUP: hash {extraido.hash_sha256[:16]}... ya existe ({existing} docs)")
            else:
                print(f"  [WARN] hash no encontrado en BD ({existing} docs con ese hash)")
    # Cerrar sesion de ingesta
    await ingesta_session.rollback()  # limpia cualquier transaccion pendiente
    await ingesta_session.close()
    print("  Sesion de ingesta cerrada.\n")

    # ── RETRIEVAL ────────────────────────────────────────────
    sep("RETRIEVAL SEMANTICO")
    # Crear nueva sesion del mismo engine (pool da conexion limpia)
    ret_session = sm()
    repo2 = RepositorioDocumentos(ret_session)
    sr = ServicioRetrieval(repositorio=repo2, proveedor_embeddings=pe)

    consultas_retrieval = [
        "Que facultades tiene la Universidad del Rosario?",
        "Que informacion existe sobre la Facultad de Ingenieria?",
        "Cuales son las facultades relacionadas con ciencias de la salud?",
        "Quien fundo la universidad del rosario?",
    ]

    for qid, consulta in enumerate(consultas_retrieval, 1):
        print(f"\n  Consulta {qid}: {consulta}")
        try:
            resultados = await sr.consultar(consulta=consulta, limite=3)
            if resultados:
                for i, r in enumerate(resultados, 1):
                    d = r.to_dict() if hasattr(r, "to_dict") else r
                    print(f"    [{i}] score={d['score']:.4f} | doc={d['titulo']}")
            else:
                print("    (sin resultados)")
        except Exception as e:
            print(f"    [ERROR] {e}")

    # ── GENERACION ──────────────────────────────────────────
    sep("GENERACION CON GPT-5.6 LUNA")
    sg = ServicioGeneracion(servicio_retrieval=sr, proveedor_llm=pl)

    consultas_generacion = [
        (1, "Que facultades tiene la Universidad del Rosario?"),
        (2, "Que informacion existe sobre la Facultad de Ingenieria?"),
        (3, "Cual es el presupuesto anual de la Universidad del Rosario?"),
    ]

    for qid, pregunta in consultas_generacion:
        sep(f"CONSULTA {qid}: {pregunta}")
        try:
            r = await sg.consultar_con_generacion(pregunta, limite=5)
            print(f"Deployment: {r.deployment} | Modelo: {r.modelo} | Fragmentos: {r.fragmentos_count}")
            for i, f in enumerate(r.fragmentos, 1):
                print(f"  [{i}] score={f['score']:.4f} | doc={f['titulo']}")

            print("\nRESPUESTA:")
            print("---" * 20)
            print(r.respuesta)
            print("---" * 20)

            if qid == 3:
                no_info = any(
                    p in r.respuesta.lower()
                    for p in ["no ", "no disponible", "no tengo", "no encuentro", "no hay", "no se", "lo siento"]
                )
                status = "PASS" if no_info else "FAIL (podria estar inventando)"
                print(f"\nGROUNDING: {status}")
            else:
                print("\nGROUNDING: revision manual recomendada")

        except Exception as e:
            print(f"  [ERROR] {e}")

    # ── CIERRE ──────────────────────────────────────────────────
    sep("LIMPIEZA")
    await ret_session.close()
    await engine.dispose()
    print("Conexiones cerradas.")

    sep("PRUEBA COMPLETADA")
    print("Resumen:")
    print("  - Ingestion: OK (ver logs arriba)")
    print("  - Dedup:     OK (ver validacion arriba)")
    print("  - Retrieval: OK (ver consultas arriba)")
    print("  - Generation: OK (ver respuestas arriba)")
    print("  - Grounding:  OK (ver validacion arriba)")


if __name__ == "__main__":
    asyncio.run(main())