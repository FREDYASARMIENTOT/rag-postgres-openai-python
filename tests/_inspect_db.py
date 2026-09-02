"""Script de inspección — Fase F."""
import sys, os, asyncio
sys.path.insert(0, "src/backend")
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from fastapi_app.postgres_engine import create_postgres_engine

async def run():
    engine = await create_postgres_engine(
        host=os.environ["POSTGRES_HOST"],
        username=os.environ["POSTGRES_USERNAME"],
        database=os.environ["POSTGRES_DATABASE"],
        password=os.environ.get("POSTGRES_PASSWORD"),
        sslmode=os.environ.get("POSTGRES_SSL", "require"),
    )
    async with engine.connect() as c:
        # 1. Legacy columns
        print("=== COLUMNAS LEGACY ===")
        rows = await c.execute(text("SELECT column_name, data_type, udt_name, character_maximum_length, is_nullable, column_default FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('documentos','fragmentos_documento') ORDER BY table_name, ordinal_position"))
        for r in rows:
            print(f"{r.table_name}.{r.column_name}: {r.data_type}({r.udt_name}) nullable={r.is_nullable} default={r.column_default}")
        # 2. Counts
        r = await c.execute(text("SELECT COUNT(*) FROM public.documentos"))
        print(f"\nDocumentos count: {r.scalar()}")
        r = await c.execute(text("SELECT COUNT(*) FROM public.fragmentos_documento"))
        print(f"Fragmentos count: {r.scalar()}")
        r = await c.execute(text("SELECT COUNT(*) FROM public.fragmentos_documento WHERE embedding IS NOT NULL"))
        print(f"Fragmentos con embedding: {r.scalar()}")
        # 3. Documents
        rows = await c.execute(text("SELECT id, titulo, fuente, tipo_documento, estado FROM public.documentos LIMIT 5"))
        print("\n=== DOCUMENTOS ===")
        for r in rows:
            print(f"id={r.id} titulo={r.titulo} fuente={r.fuente} tipo={r.tipo_documento} estado={r.estado}")
        # 4. Fragments
        rows = await c.execute(text("SELECT id, documento_id, orden FROM public.fragmentos_documento ORDER BY id LIMIT 5"))
        print("\n=== FRAGMENTOS ===")
        for r in rows:
            print(f"id={r.id} doc_id={r.documento_id} orden={r.orden}")
        # 5. Embedding type
        r = await c.execute(text("SELECT pg_typeof(e.embedding) FROM public.fragmentos_documento e WHERE e.embedding IS NOT NULL LIMIT 1"))
        print(f"\npg_typeof(embedding): {r.scalar()}")
        # 6. Indexes
        rows = await c.execute(text("SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename IN ('documentos','fragmentos_documento')"))
        print("\n=== INDICES ===")
        for r in rows:
            print(f"{r.tablename}.{r.indexname}: {r.indexdef}")
        # 7. FK
        rows = await c.execute(text("SELECT tc.constraint_name, tc.table_name, kcu.column_name, ccu.table_name AS ftable, ccu.column_name AS fcolumn FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' AND tc.table_name IN ('documentos','fragmentos_documento')"))
        print("\n=== FOREIGN KEYS ===")
        for r in rows:
            print(f"{r.table_name}.{r.column_name} -> {r.ftable}.{r.fcolumn} ({r.constraint_name})")
        # 8. Comments
        rows = await c.execute(text("SELECT c.table_name, c.column_name, pgd.description FROM pg_catalog.pg_statio_all_tables st INNER JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid RIGHT JOIN information_schema.columns c ON pgd.objsubid = c.ordinal_position AND c.table_name = st.relname WHERE c.table_schema='public' AND c.table_name IN ('documentos','fragmentos_documento') ORDER BY c.table_name, c.ordinal_position"))
        print("\n=== COMMENTS ===")
        found = False
        for r2 in rows:
            if r2.description:
                found = True
                print(f"{r2.table_name}.{r2.column_name}: {r2.description[:100]}")
        if not found:
            print("(no comments)")
    await engine.dispose()

asyncio.run(run())
# 3. Indexes
        rows = await conn.execute(text(
            "SELECT tablename, indexname, indexdef FROM pg_indexes "
            "WHERE schemaname='public' AND tablename IN ('documentos','fragmentos_documento')"))
        print("\n=== INDICES ===")
        for r in rows:
            print(f"{r.tablename}.{r.indexname}: {r.indexdef}")

        # 4. Counts
        r = await conn.execute(text("SELECT COUNT(*) FROM public.documentos"))
        print(f"\nDocumentos count: {r.scalar()}")
        r = await conn.execute(text("SELECT COUNT(*) FROM public.fragmentos_documento"))
        print(f"Fragmentos count: {r.scalar()}")
        r = await conn.execute(text("SELECT COUNT(*) FROM public.fragmentos_documento WHERE embedding IS NOT NULL"))
        print(f"Fragmentos con embedding: {r.scalar()}")

        # 5. Documents
        rows = await conn.execute(text(
            "SELECT id, titulo, fuente, tipo_documento, estado FROM public.documentos LIMIT 5"))
        print("\n=== DOCUMENTOS ===")
        for r in rows:
            print(f"id={r.id} titulo={r.titulo} fuente={r.fuente} tipo={r.tipo_documento} estado={r.estado}")

        # 6. Fragments
        rows = await conn.execute(text(
            "SELECT id, documento_id, orden FROM public.fragmentos_documento ORDER BY id LIMIT 5"))
        print("\n=== FRAGMENTOS ===")
        for r in rows:
            print(f"id={r.id} doc_id={r.documento_id} orden={r.orden}")

        # 7. Comments
        rows = await conn.execute(text(
            "SELECT c.table_name, c.column_name, pgd.description "
            "FROM pg_catalog.pg_statio_all_tables st "
            "INNER JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid "
            "RIGHT JOIN information_schema.columns c "
            "ON pgd.objsubid = c.ordinal_position AND c.table_name = st.relname "
            "WHERE c.table_schema='public' AND c.table_name IN ('documentos','fragmentos_documento') "
            "ORDER BY c.table_name, c.ordinal_position"))
        print("\n=== COMMENTS ===")
        found = False
        for r2 in rows:
            if r2.description:
                found = True
                print(f"{r2.table_name}.{r2.column_name}: {r2.description[:100]}")
        if not found:
            print("(no comments found)")

        # 8. Embedding type
        rows = await conn.execute(text(
            "SELECT e.column_name, e.udt_name FROM information_schema.columns e "
            "WHERE e.table_schema='public' AND e.table_name='fragmentos_documento' "
            "AND e.column_name='embedding'"))
        for r2 in rows:
            print(f"\nEmbedding column: {r2.column_name} type={r2.udt_name}")
        r = await conn.execute(text(
            "SELECT pg_typeof(e.embedding) FROM public.fragmentos_documento e "
            "WHERE e.embedding IS NOT NULL LIMIT 1"))
        tv = r.scalar()
        print(f"pg_typeof(embedding): {tv}")

        # 9. Foreign keys
        rows = await conn.execute(text(
            "SELECT tc.constraint_name, tc.table_name, kcu.column_name, "
            "ccu.table_name AS ftable, ccu.column_name AS fcolumn "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name "
            "JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name "
            "WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public' "
            "AND tc.table_name IN ('documentos','fragmentos_documento')"))
        print("\n=== FOREIGN KEYS ===")
        for r2 in rows:
            print(f"{r2.table_name}.{r2.column_name} -> {r2.ftable}.{r2.fcolumn} ({r2.constraint_name})")

    await engine.dispose()

asyncio.run(inspect())