from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount, Route, Router

parent_dir = Path(__file__).resolve().parent.parent.parent


async def index(request) -> FileResponse:
    return FileResponse(parent_dir / "static/index.html")


async def favicon(request):
    return FileResponse(parent_dir / "static/favicon.ico")


# ── PoC Institutional RAG ──
POC_STATIC = parent_dir / "poc-static"


async def poc_index(request) -> FileResponse:
    return FileResponse(POC_STATIC / "index.html")


POC_ASSETS = StaticFiles(directory=POC_STATIC / "assets", check_dir=False)


# Build routes dynamically: only mount directories if they exist
STATIC_DIR = parent_dir / "static/assets"
routes = [
    Route("/", endpoint=index),
    Route("/favicon.ico", endpoint=favicon),
]

if STATIC_DIR.exists():
    routes.append(Mount("/assets", app=StaticFiles(directory=STATIC_DIR), name="static_assets"))

if POC_STATIC.exists() and (POC_STATIC / "index.html").exists():
    routes.append(Route("/poc", endpoint=poc_index))
    routes.append(Route("/poc/", endpoint=poc_index))
    routes.append(Mount("/poc/assets", app=POC_ASSETS, name="poc_static_assets"))

router = Router(routes=routes)
