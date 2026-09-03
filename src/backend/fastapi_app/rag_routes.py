"""
FastAPI routes para el RAG Institucional — Universidad del Rosario.

Propósito:
    Expone endpoints HTTP que envuelven los servicios internos del RAG
    Institucional (ServicioRetrieval, ServicioGeneracion, ServicioIngesta)
    para ser consumidos por el frontend React PoC local.

Contexto arquitectónico:
    Frontend React Local
        ↓ HTTP
    FASTAPI LOCAL (ESTE MODULO)
        ↓
    Servicios RAG Institucional
        ├── ServicioIngesta
        ├── ServicioRetrieval
        └── ServicioGeneracion
        ↓
    PostgreSQL + pgvector + Azure AI Foundry

    El MCP Server es una interfaz alternativa para agentes IA.
    Estas rutas son la interfaz HTTP directa para el frontend.

Uso:
    Registrado automáticamente en fastapi_app/__init__.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker

from fastapi_app.proveedores import ProveedorEmbeddings, ProveedorLLM
from fastapi_app.repositorio_documentos import RepositorioDocumentos
from fastapi_app.servicio_generacion import ServicioGeneracion
from fastapi_app.servicio_ingesta import ServicioIngesta
from fastapi_app.servicio_retrieval import ServicioRetrieval

logger = logging.getLogger("ragapp")

router = APIRouter(prefix="/api/rag", tags=["rag-institucional"])


# =============================================================================
# MODELOS DE SOLICITUD / RESPUESTA
# =============================================================================


class ConsultaRequest(BaseModel):
    consulta: str = Field(..., min_length=1, description="Pregunta en lenguaje natural")
    limite: int = Field(default=10, ge=1, le=50, description="Máximo de fragmentos")
    usuario: str = Field(default="frontend-poc", description="Identificador del usuario")


class ConsultaResponse(BaseModel):
    consulta: str
    resultados: list[dict]
    total: int


class ConsultaGeneracionRequest(BaseModel):
    consulta: str = Field(..., min_length=1, description="Pregunta en lenguaje natural")
    limite: int = Field(default=5, ge=1, le=10, description="Máximo de fragmentos para contexto")
    usuario: str = Field(default="frontend-poc", description="Identificador del usuario")


class ConsultaGeneracionResponse(BaseModel):
    consulta: str
    respuesta: str
    fragmentos_count: int
    deployment: str
    modelo: str
    fragmentos: list[dict]


class IngestarContenidoRequest(BaseModel):
    titulo: str = Field(..., min_length=1, description="Título del documento")
    contenido: str = Field(..., min_length=1, description="Contenido en texto plano o Markdown")
    fuente: str = Field(default="manual", description="Fuente del documento")
    tipo_documento: str = Field(default="general")
    usuario: str = Field(default="frontend-poc")


class IngestarArchivoRequest(BaseModel):
    ruta_archivo: str = Field(..., min_length=1, description="Ruta absoluta al archivo en el servidor")
    fuente: str = Field(default="archivo-local", description="Fuente del documento")
    tipo_documento: str = Field(default="general")
    usuario: str = Field(default="frontend-poc")


class DocumentoItem(BaseModel):
    documento_id: int
    titulo: str
    fuente: str
    tipo_documento: str
    estado: str
    nombre_archivo_original: Optional[str] = None
    extension_archivo: Optional[str] = None
    cantidad_fragmentos: int = 0
    fecha_creacion: Optional[str] = None


class DocumentoDetalle(BaseModel):
    documento_id: int
    titulo: str
    fuente: str
    tipo_documento: str
    estado: str
    nombre_archivo_original: Optional[str] = None
    extension_archivo: Optional[str] = None
    cantidad_paginas: Optional[int] = None
    cantidad_fragmentos: int = 0
    fragmentos: list[dict]


# =============================================================================
# DEPENDENCIAS (creación per-request con sesión fresca)
# =============================================================================


def _get_sessionmaker(request: Request) -> async_sessionmaker:
    sm = getattr(request.app.state, "sessionmaker", None)
    if sm is None:
        raise HTTPException(status_code=503, detail="sessionmaker no disponible")
    return sm


def _get_rag_proveedor_embeddings(request: Request) -> Optional[ProveedorEmbeddings]:
    return getattr(request.app.state, "rag_proveedor_embeddings", None)


def _get_rag_proveedor_llm(request: Request) -> Optional[ProveedorLLM]:
    return getattr(request.app.state, "rag_proveedor_llm", None)


# =============================================================================
# HEALTHCHECK
# =============================================================================


async def _crear_servicios(
    request: Request,
) -> tuple[RepositorioDocumentos, ServicioRetrieval, Optional[ServicioGeneracion], ServicioIngesta]:
    """Crea servicios institucionales con una sesión fresca."""
    sm = _get_sessionmaker(request)
    proveedor_emb = _get_rag_proveedor_embeddings(request)
    proveedor_llm = _get_rag_proveedor_llm(request)
    session = sm()
    repositorio = RepositorioDocumentos(session)
    servicio_retrieval = ServicioRetrieval(repositorio=repositorio, proveedor_embeddings=proveedor_emb)
    servicio_generacion = None
    if proveedor_llm:
        servicio_generacion = ServicioGeneracion(
            servicio_retrieval=servicio_retrieval,
            proveedor_llm=proveedor_llm,
        )
    servicio_ingesta = ServicioIngesta(repositorio=repositorio, proveedor_embeddings=proveedor_emb)
    return repositorio, servicio_retrieval, servicio_generacion, servicio_ingesta


@router.get("/health")
async def health_check(request: Request):
    sm = _get_sessionmaker(request)
    proveedor_emb = _get_rag_proveedor_embeddings(request)
    proveedor_llm = _get_rag_proveedor_llm(request)
    return {
        "status": "ok",
        "sessionmaker": sm is not None,
        "proveedor_embeddings": proveedor_emb is not None,
        "proveedor_llm": proveedor_llm is not None,
    }


# =============================================================================
# CONSULTA (retrieval puro)
# =============================================================================


@router.post("/consulta", response_model=ConsultaResponse)
async def consultar_rag(request: Request, body: ConsultaRequest):
    _, servicio_retrieval, _, _ = await _crear_servicios(request)
    try:
        resultados = await servicio_retrieval.consultar(consulta=body.consulta, limite=body.limite)
        return ConsultaResponse(
            consulta=body.consulta,
            resultados=[r.to_dict() for r in resultados],
            total=len(resultados),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Error en consulta RAG: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# =============================================================================
# CONSULTA CON GENERACION
# =============================================================================


@router.post("/consultar-con-generacion", response_model=ConsultaGeneracionResponse)
async def consultar_con_generacion(request: Request, body: ConsultaGeneracionRequest):
    _, servicio_retrieval, servicio_generacion, _ = await _crear_servicios(request)
    if servicio_generacion is None:
        resultados = await servicio_retrieval.consultar(consulta=body.consulta, limite=body.limite)
        return ConsultaGeneracionResponse(
            consulta=body.consulta,
            respuesta="[ServicioGeneracion no disponible. Solo resultados de busqueda.]",
            fragmentos_count=len(resultados),
            deployment="",
            modelo="",
            fragmentos=[r.to_dict() for r in resultados],
        )
    try:
        resultado = await servicio_generacion.consultar_con_generacion(
            consulta=body.consulta, limite=body.limite,
        )
        return ConsultaGeneracionResponse(
            consulta=resultado.consulta,
            respuesta=resultado.respuesta,
            fragmentos_count=resultado.fragmentos_count,
            deployment=resultado.deployment,
            modelo=resultado.modelo,
            fragmentos=resultado.fragmentos,
        )
    except Exception as e:
        logger.error("Error en generacion RAG: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en generacion: {e}")


# =============================================================================
# INGESTA DE CONTENIDO (texto plano)
# =============================================================================


@router.post("/cargar-contenido")
async def cargar_contenido_rag(request: Request, body: IngestarContenidoRequest):
    _, _, _, servicio_ingesta = await _crear_servicios(request)
    try:
        resultado = await servicio_ingesta.ingestar(
            titulo=body.titulo, contenido=body.contenido,
            fuente=body.fuente, tipo_documento=body.tipo_documento,
            usuario_cargador=body.usuario,
        )
        return {"status": "ok", "resultado": resultado.to_dict()}
    except Exception as e:
        logger.error("Error en ingesta: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en ingesta: {e}")


# =============================================================================
# INGESTA DESDE ARCHIVO EN SERVIDOR
# =============================================================================


@router.post("/ingestar-archivo")
async def ingestar_archivo(request: Request, body: IngestarArchivoRequest):
    _, _, _, servicio_ingesta = await _crear_servicios(request)
    ruta = Path(body.ruta_archivo)
    if not ruta.exists():
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {body.ruta_archivo}")
    if not ruta.is_file():
        raise HTTPException(status_code=400, detail=f"No es un archivo: {body.ruta_archivo}")
    try:
        resultado = await servicio_ingesta.ingestar_desde_archivo(
            ruta_archivo=str(ruta.resolve()),
            fuente=body.fuente, tipo_documento=body.tipo_documento,
            usuario_cargador=body.usuario,
        )
        return {"status": "ok", "resultado": resultado.to_dict()}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error en ingesta de archivo: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en ingesta: {e}")


# =============================================================================
# LISTAR DOCUMENTOS
# =============================================================================


@router.get("/documentos", response_model=list[DocumentoItem])
async def listar_documentos(request: Request):
    repo, _, _, _ = await _crear_servicios(request)
    try:
        docs = await repo.listar_documentos()
        items = []
        for doc in docs:
            try:
                fragmentos = await repo.obtener_fragmentos_por_documento(doc.id_documento)
                cant_frags = len(fragmentos) if fragmentos else 0
            except Exception:
                cant_frags = 0
            fecha_str = None
            if hasattr(doc, "fecha_creacion") and doc.fecha_creacion:
                fecha_str = str(doc.fecha_creacion)
            items.append(DocumentoItem(
                documento_id=doc.id_documento,
                titulo=doc.titulo_documento,
                fuente=doc.fuente_documento,
                tipo_documento=doc.tipo_documento,
                estado=doc.estado_vigencia,
                nombre_archivo_original=doc.nombre_archivo_original,
                extension_archivo=doc.extension_archivo,
                cantidad_fragmentos=cant_frags,
                fecha_creacion=fecha_str,
            ))
        return items
    except Exception as e:
        logger.error("Error listando documentos: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al listar documentos: {e}")


# =============================================================================
# DETALLE DE DOCUMENTO
# =============================================================================


@router.get("/documento/{documento_id}", response_model=DocumentoDetalle)
async def obtener_documento(request: Request, documento_id: int):
    repo, _, _, _ = await _crear_servicios(request)
    try:
        doc = await repo.obtener_documento_por_id(documento_id)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Documento {documento_id} no encontrado")
        fragmentos = await repo.obtener_fragmentos_por_documento(documento_id)
        return DocumentoDetalle(
            documento_id=doc.id_documento,
            titulo=doc.titulo_documento,
            fuente=doc.fuente_documento,
            tipo_documento=doc.tipo_documento,
            estado=doc.estado_vigencia,
            nombre_archivo_original=doc.nombre_archivo_original,
            extension_archivo=doc.extension_archivo,
            cantidad_paginas=doc.cantidad_paginas,
            cantidad_fragmentos=len(fragmentos) if fragmentos else 0,
            fragmentos=[
                {
                    "id_fragmento": f.id_fragmento,
                    "numero_orden": f.numero_orden,
                    "contenido": f.contenido,
                    "cantidad_caracteres": f.cantidad_caracteres,
                }
                for f in (fragmentos or [])
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error obteniendo documento: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener documento: {e}")


# =============================================================================
# ELIMINAR DOCUMENTO
# =============================================================================


@router.delete("/documento/{documento_id}")
async def eliminar_documento(request: Request, documento_id: int):
    repo, _, _, _ = await _crear_servicios(request)
    try:
        if documento_id <= 0:
            raise HTTPException(status_code=400, detail="documento_id debe ser positivo")
        eliminado = await repo.eliminar_documento(documento_id)
        if not eliminado:
            raise HTTPException(status_code=404, detail=f"Documento {documento_id} no encontrado")
        return {"status": "ok", "mensaje": f"Documento {documento_id} eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error eliminando documento: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al eliminar documento: {e}")


# =============================================================================
# DOCUMENTOS DE EJEMPLO DISPONIBLES
# =============================================================================


@router.get("/documentos-ejemplo")
async def listar_documentos_ejemplo():
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    ejemplos_dir = base_dir / "documentos_ejemplo"
    if not ejemplos_dir.exists():
        return {"archivos": [], "ruta_base": str(ejemplos_dir)}
    archivos = []
    for ext in ["*.md", "*.pdf", "*.txt"]:
        archivos.extend([str(p.relative_to(ejemplos_dir)) for p in ejemplos_dir.rglob(ext)])
    return {"archivos": sorted(archivos), "ruta_base": str(ejemplos_dir.resolve())}