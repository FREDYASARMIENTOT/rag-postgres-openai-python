"""
Script de auditoria de base de datos real para Fase F.1.
INSPECCIONAR -> COMPRENDER -> VALIDAR -> PROPONER

Proposito:
    Comprueba el estado real de PostgreSQL sin modificar nada.
    Verifica schemas, tablas, columnas, tipos, constraints, indices, comentarios.

Uso:
    python db/auditar_bd.py

Seguridad:
    - Solo lectura (SELECT)
    - No modifica nada
    - No muestra secretos
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "backend"))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

logger = logging.getLogger("auditar_bd")

OK = "  [OK]"
FAIL = "  [FAIL]"
WARN = "  [WARN]"
INFO = "  [INFO]"

def sep(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


async def get_engine():
    host = os.environ["POSTGRES_HOST"]
    username = os.environ["POSTGRES_USERNAME"]
    database = os.environ["POSTGRES_DATABASE"]
    password = os.environ.get("POSTGRES_PASSWORD") or ""
    sslmode = os.environ.get("POSTGRES_SSL", "require")

    if host.endswith(".database.azure.com"):
        from azure.identity import DefaultAzureCredential
        try:
            credential = DefaultAzureCredential()
            token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
            if token:
                password = token.token
        except Exception as e:
            logger.warning("No se pudo obtener token Azure AD: %s", e)

    from urllib.parse import quote
    user_encoded = quote(username)
    pass_encoded = quote(password)

    db_url = f"postgresql+asyncpg://{user_encoded}:{pass_encoded}@{host}:5432/{database}"
    if host.endswith(".database.azure.com"):
        db_url += "?ssl=require"
    return create_async_engine(db_url, echo=False)
async def auditar():
    print("\n" + "#" * 70)
    print("  AUDITORIA DE BASE DE DATOS - FASE F.1")
    print("  RAG Institucional - Universidad del Rosario")
    print("  100% SOLO LECTURA - NO MODIFICA NADA")
    print("#" * 70)

    engine = await get_engine()
    async with engine.connect() as conn:

        sep("A. INFORMACION GENERAL")
        row = await conn.execute(text("SELECT current_database()"))
        print(f"  Base de datos actual: {row.scalar()}")
        row = await conn.execute(text("SELECT version()"))
        ver = row.scalar()
        print(f"  Version PostgreSQL: {ver.split(',')[0] if ver else ver}")
        row = await conn.execute(text("SELECT current_user"))
        print(f"  Usuario conectado: {row.scalar()}")

        sep("B. EXTENSION VECTOR (pgvector)")
        row = await conn.execute(
            text("SELECT TRUE FROM pg_available_extensions WHERE name = 'vector'")
        )
        print(f"{OK if row.scalar() else FAIL} pgvector disponible en servidor")
        row = await conn.execute(
            text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
        )
        ext = row.fetchone()
        if ext:
            print(f"{OK} pgvector HABILITADO: {ext[0]} v{ext[1]}")
        else:
            print(f"{FAIL} pgvector NO habilitado (CREATE EXTENSION pendiente)")

        sep("C. SCHEMAS EXISTENTES")
        rows = await conn.execute(
            text("""
                SELECT schema_name FROM information_schema.schemata
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name
            """)
        )
        schemas = [r[0] for r in rows.fetchall()]
        print(f"  Schemas: {schemas}")
        print(f"{OK if 'rag' in schemas else FAIL} Schema 'rag'")
        print(f"{OK if 'log' in schemas else FAIL} Schema 'log'")
        print(f"{OK if 'public' in schemas else WARN} Schema 'public'")
        TABLAS_RAG = [
            "series_documentales", "temas", "periodos",
            "documentos", "documentos_temas", "fragmentos_documento",
        ]
        TABLAS_LOG = [
            "cargas_documentos", "consultas",
            "consultas_documentos", "consultas_fragmentos", "eventos_documentos",
        ]

        rows = await conn.execute(
            text("""
                SELECT table_schema, table_name FROM information_schema.tables
                WHERE table_schema IN ('rag', 'log')
                ORDER BY table_schema, table_name
            """)
        )
        existing = {(r.table_schema, r.table_name) for r in rows.fetchall()}

        sep("D. TABLAS rag")
        for t in TABLAS_RAG:
            print(f"{OK if ('rag', t) in existing else FAIL} rag.{t}")

        sep("D. TABLAS log")
        for t in TABLAS_LOG:
            print(f"{OK if ('log', t) in existing else FAIL} log.{t}")

        sep("E. TABLAS LEGACY (public)")
        rows = await conn.execute(
            text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('documentos', 'fragmentos_documento')
            """)
        )
        legacy = {r[0] for r in rows.fetchall()}
        for t in ["documentos", "fragmentos_documento"]:
            print(f"{OK if t in legacy else FAIL} public.{t}")

        sep("F. VERIFICACION superset")
        row = await conn.execute(
            text("SELECT datname FROM pg_database WHERE datname = 'superset'")
        )
        print(f"{OK if row.scalar() else WARN} BD 'superset' existe")
        if 'rag' in schemas:
            sep("G. ESTRUCTURA rag.fragmentos_documento")
            if ('rag', 'fragmentos_documento') in existing:
                rows = await conn.execute(
                    text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = 'rag' AND table_name = 'fragmentos_documento'
                        ORDER BY ordinal_position
                    """)
                )
                for r in rows.fetchall():
                    tipo = r.data_type
                    print(f"    {r.column_name:30s} {tipo:20s} {'NOT NULL' if r.is_nullable == 'NO' else ''} {r.column_default or ''}")

            sep("H. VERIFICACION VECTOR(3072)")
            if ('rag', 'fragmentos_documento') in existing:
                row = await conn.execute(
                    text("""
                        SELECT column_name, udt_name
                        FROM information_schema.columns
                        WHERE table_schema = 'rag' AND table_name = 'fragmentos_documento'
                        AND column_name = 'embedding'
                    """)
                )
                col = row.fetchone()
                if col:
                    row_dim = await conn.execute(
                        text("""
                            SELECT atttypmod FROM pg_attribute
                            WHERE attrelid = 'rag.fragmentos_documento'::regclass
                            AND attname = 'embedding' AND attnum > 0
                        """)
                    )
                    dim = row_dim.fetchone()
                    dim_val = dim[0] if dim else 0
                    label = f"{OK if dim_val == 3072 else FAIL} embedding: {col.udt_name} (dimension={dim_val})"
                    print(label)
                else:
                    print(f"{FAIL} Columna 'embedding' NO encontrada")

            sep("I. COLUMNAS DATE/TIME")
            for schema_name in ['rag', 'log']:
                rows = await conn.execute(
                    text(f"""
                        SELECT table_name, column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = '{schema_name}'
                        AND data_type IN ('date', 'time without time zone')
                        ORDER BY table_name, ordinal_position
                    """)
                )
                cols = rows.fetchall()
                if cols:
                    print(f"  Schema {schema_name}:")
                    for c in cols:
                        tipo_str = "TIME" if "time" in c.data_type else "DATE"
                        print(f"    {c.table_name}.{c.column_name}: {tipo_str}")

            sep("J. FOREIGN KEYS")
            rows = await conn.execute(
                text("""
                    SELECT tc.table_schema, tc.table_name, kcu.column_name,
                           ccu.table_schema AS ref_schema, ccu.table_name AS ref_table,
                           ccu.column_name AS ref_column, rc.delete_rule
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                        AND tc.table_schema = ccu.table_schema
                    JOIN information_schema.referential_constraints rc
                        ON tc.constraint_name = rc.constraint_name
                        AND tc.table_schema = rc.constraint_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema IN ('rag', 'log')
                    ORDER BY tc.table_schema, tc.table_name
                """)
            )
            fks = rows.fetchall()
            if fks:
                for fk in fks:
                    print(f"  {fk.table_schema}.{fk.table_name}.{fk.column_name} -> {fk.ref_schema}.{fk.ref_table}.{fk.ref_column} [ON DELETE {fk.delete_rule}]")
            else:
                print(f"{INFO} No se encontraron FK")

            sep("K. UNIQUE CONSTRAINTS")
            rows = await conn.execute(
                text("""
                    SELECT tc.table_schema, tc.table_name, tc.constraint_name
                    FROM information_schema.table_constraints tc
                    WHERE tc.constraint_type = 'UNIQUE'
                    AND tc.table_schema IN ('rag')
                    ORDER BY tc.table_schema, tc.table_name
                """)
            )
            uniques = rows.fetchall()
            if uniques:
                for u in uniques:
                    print(f"  {u.table_schema}.{u.table_name}: {u.constraint_name}")
            else:
                print(f"{INFO} No UNIQUE constraints en rag")

            sep("L. INDICES")
            rows = await conn.execute(
                text("""
                    SELECT schemaname, tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname IN ('rag', 'log')
                    ORDER BY schemaname, tablename, indexname
                """)
            )
            indices = rows.fetchall()
            if indices:
                for idx in indices:
                    print(f"  {idx.schemaname}.{idx.tablename}: {idx.indexname}")
            else:
                print(f"{INFO} No indices en rag/log")

            sep("M. COMENTARIOS POSTGRESQL")
            rows = await conn.execute(
                text("""
                    SELECT n.nspname AS schema_name, c.relname AS obj_name,
                           CASE c.relkind WHEN 'r' THEN 'TABLE' ELSE 'OTHER' END AS obj_type,
                           pgd.description
                    FROM pg_catalog.pg_description pgd
                    JOIN pg_catalog.pg_class c ON pgd.objoid = c.oid
                    JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                    WHERE n.nspname IN ('rag', 'log') AND pgd.objsubid = 0
                    ORDER BY n.nspname, c.relname
                """)
            )
            comments = rows.fetchall()
            if comments:
                for cm in comments:
                    ok = OK if cm.description else FAIL
                    print(f"{ok} {cm.schema_name}.{cm.obj_name} ({cm.obj_type})")
                    if cm.description:
                        print(f"     -> {cm.description[:100]}")
            else:
                print(f"{INFO} No comments en rag/log")

            rows = await conn.execute(
                text("""
                    SELECT n.nspname, c.relname, a.attname, pgd.description
                    FROM pg_catalog.pg_description pgd
                    JOIN pg_catalog.pg_class c ON pgd.objoid = c.oid
                    JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                    JOIN pg_catalog.pg_attribute a ON (pgd.objoid, pgd.objsubid) = (a.attrelid, a.attnum)
                    WHERE n.nspname IN ('rag', 'log') AND pgd.objsubid > 0
                    ORDER BY n.nspname, c.relname, a.attnum
                    LIMIT 15
                """)
            )
            col_comments = rows.fetchall()
            if col_comments:
                print(f"\n  Comentarios de columna: {len(col_comments)} encontrados (primeros 15)")
                for cm in col_comments:
                    desc = cm.description[:80] if cm.description else "SIN COMENTARIO"
                    print(f"  {cm.nspname}.{cm.relname}.{cm.attname}: {desc}")

    await engine.dispose()
    print("\n" + "#" * 70)
    print("  AUDITORIA COMPLETADA - SOLO LECTURA")
    print("#" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(auditar())
