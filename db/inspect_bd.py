import asyncio, os, asyncpg, json
from dotenv import load_dotenv
load_dotenv()

async def main():
    host = os.environ['POSTGRES_HOST']; u = os.environ['POSTGRES_USERNAME']
    db = os.environ['POSTGRES_DATABASE']; p = os.environ.get('POSTGRES_PASSWORD','') or ''
    ssl = os.environ.get('POSTGRES_SSL','require')
    if host.endswith('.database.azure.com') and not p:
        from azure.identity import DefaultAzureCredential
        cred = DefaultAzureCredential(); tok = cred.get_token('https://ossrdbms-aad.database.windows.net/.default'); p = tok.token
    conn = await asyncpg.connect(host=host, port=5432, user=u, password=p, database=db, ssl=ssl)
    
    rows = await conn.fetch("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
    print(f'SCHEMAS: {[r[0] for r in rows]}')
    
    for sch in ['rag','log']:
        rows = await conn.fetch(f"SELECT table_name FROM information_schema.tables WHERE table_schema='{sch}' ORDER BY table_name")
        print(f'{sch.upper()} TABLAS: {[r[0] for r in rows]}')
        for tbl in [r[0] for r in rows]:
            cols = await conn.fetch(f"SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='{sch}' AND table_name='{tbl}' ORDER BY ordinal_position")
            print(f'  {tbl} ({len(cols)} cols):')
            for c in cols:
                d = str(c[3])[:40] if c[3] else ''
                print(f'    {c[0]:30s} {c[1]:15s} null={c[2]} def={d}')
    
    # Constraints
    rows = await conn.fetch("SELECT conname, pg_get_constraintdef(con.oid) FROM pg_catalog.pg_constraint con JOIN pg_catalog.pg_class rel ON rel.oid=con.conrelid JOIN pg_catalog.pg_namespace nsp ON nsp.oid=rel.relnamespace WHERE nsp.nspname='rag'")
    print('CONSTRAINTS rag:')
    for r in rows: print(f'  {r[0]}: {r[1][:100]}')
    
    # Indices
    rows = await conn.fetch("SELECT indexname,schemaname FROM pg_indexes WHERE schemaname IN ('rag','log') ORDER BY indexname")
    print(f'INDICES: {[(r[0],r[1]) for r in rows]}')
    
    # Counts
    for sch in ['rag','log']:
        tbls = await conn.fetch(f"SELECT table_name FROM information_schema.tables WHERE table_schema='{sch}' ORDER BY table_name")
        for t in tbls:
            c = await conn.fetchval(f"SELECT COUNT(*) FROM {sch}.{t[0]}")
            print(f'  {sch}.{t[0]}: {c} rows')
    
    if await conn.fetchval('SELECT COUNT(*) FROM rag.documentos') > 0:
        rows = await conn.fetch('SELECT * FROM rag.documentos LIMIT 2')
        for r in rows:
            d = dict(r)
            print(f'  DOC: {json.dumps(d, default=str)[:400]}')
    
    if await conn.fetchval('SELECT COUNT(*) FROM rag.fragmentos_documento') > 0:
        rows = await conn.fetch('SELECT id_fragmento,id_documento,numero_orden,cantidad_caracteres,embedding IS NOT NULL as has_emb FROM rag.fragmentos_documento LIMIT 3')
        for r in rows:
            print(f'  FRAG: {dict(r)}')
    
    # Extensiones
    rows = await conn.fetch("SELECT extname,extversion FROM pg_extension ORDER BY extname")
    print(f'EXTENSIONES: {[(r[0],r[1]) for r in rows]}')
    
    await conn.close()
asyncio.run(main())