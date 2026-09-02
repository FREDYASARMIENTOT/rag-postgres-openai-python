"""
Prueba E2E real de generacion RAG con GPT-5.6 Luna.
Ejecuta el flujo completo:
    Pregunta -> Embedding -> Retrieval -> Contexto -> GPT-5.6 Luna -> Respuesta
"""
import asyncio, logging, os
from dotenv import load_dotenv
load_dotenv(override=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("test_generacion")

def sep(t: str) -> None:
    print(f"\n{'='*70}\n  {t}\n{'='*70}")

async def test_generacion() -> None:
    from fastapi_app.dependencies import common_parameters, create_async_sessionmaker, get_azure_credential
    from fastapi_app.openai_clients import create_openai_chat_client, create_openai_embed_client
    from fastapi_app.postgres_engine import create_postgres_engine_from_env
    from fastapi_app.proveedores import crear_proveedor_embeddings, crear_proveedor_llm
    from fastapi_app.repositorio_documentos import RepositorioDocumentos
    from fastapi_app.servicio_generacion import ServicioGeneracion
    from fastapi_app.servicio_retrieval import ServicioRetrieval

    sep("CONFIGURACION")
    c = await common_parameters()
    print(f"Embed: {c.rag_embed_model}/{c.rag_embed_deployment} [{c.rag_embed_dimensions}d]")
    print(f"LLM:   {c.rag_llm_model}/{c.rag_llm_deployment}")
    print(f"Host:  PG={os.getenv('POSTGRES_HOST')} Chat={c.rag_chat_host} Embed={c.rag_embed_host}")

    cred = None
    if os.getenv("POSTGRES_HOST", "").endswith(".database.azure.com"):
        cred = await get_azure_credential()
        print("Azure Credential: OK")

    sep("POSTGRESQL")
    engine = await create_postgres_engine_from_env(cred)
    sm = await create_async_sessionmaker(engine)
    print("PostgreSQL: OK")

    sep("EMBEDDINGS (FOUNDRY)")
    ec = await create_openai_embed_client(cred, host_override="foundry", deployment_override=c.rag_embed_deployment or c.rag_embed_model)
    pe = crear_proveedor_embeddings(cliente=ec, modelo=c.rag_embed_model, deployment=c.rag_embed_deployment, dimensiones=c.rag_embed_dimensions)
    print(f"Embeddings: OK ({c.rag_embed_model}, {c.rag_embed_dimensions}d)")

    sep("CHAT LUNA (FOUNDRY)")
    cc = await create_openai_chat_client(cred, host_override="foundry", deployment_override=c.rag_llm_deployment or c.rag_llm_model)
    pl = crear_proveedor_llm(cliente=cc, modelo=c.rag_llm_model, deployment=c.rag_llm_deployment)
    print(f"Luna: model={pl.modelo}, deployment={pl.deployment}")
    # Quick test
    tr = await cc.chat.completions.create(model=pl.deployment, messages=[{"role":"user","content":"OK?"}], max_completion_tokens=5)
    print(f"Luna ping: {tr.choices[0].message.content}")

    async with sm() as session:
        repo = RepositorioDocumentos(session)
        sr = ServicioRetrieval(repositorio=repo, proveedor_embeddings=pe)
        sg = ServicioGeneracion(servicio_retrieval=sr, proveedor_llm=pl)

        consultas = [
            (1, "Que facultades tiene la Universidad del Rosario?"),
            (2, "Que informacion existe sobre la Facultad de Ingenieria?"),
            (3, "Cuales son las facultades relacionadas con ciencias de la salud?"),
            (4, "Cual es el presupuesto anual de la Universidad del Rosario?"),
        ]
        for qid, pregunta in consultas:
            sep(f"CONSULTA {qid}: {pregunta}")
            r = await sg.consultar_con_generacion(pregunta, limite=5)
            print(f"Deployment: {r.deployment} | Modelo: {r.modelo} | Fragmentos: {r.fragmentos_count}")
            for i, f in enumerate(r.fragmentos, 1):
                print(f"  [{i}] score={f['score']:.4f} | doc={f['titulo']} | src={f['fuente']}")
            print("\nRESPUESTA:")
            print("-"*50, r.respuesta, "-"*50, sep="\n")
            if qid == 4:
                no_info = any(p in r.respuesta.lower() for p in ["no ", "no disponible", "no tengo", "no encuentro"])
                print("GROUNDING:", "PASS (no inventa)" if no_info else "FAIL (podria inventar)")
            else:
                print("GROUNDING: Pendiente revision manual")

    await engine.dispose()
    print("\nPRUEBA COMPLETADA - GPT-5.6 Luna real ejecutado")

if __name__ == "__main__":
    asyncio.run(test_generacion())