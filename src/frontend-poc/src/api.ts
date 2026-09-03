const API_BASE = "/api/rag";

export interface ConsultaResult {
  consulta: string;
  resultados: Array<{
    contenido: string;
    documento_id: number;
    titulo: string;
    fuente: string;
    score: number;
  }>;
  total: number;
}

export interface GeneracionResult {
  consulta: string;
  respuesta: string;
  fragmentos_count: number;
  deployment: string;
  modelo: string;
  fragmentos: Array<{
    contenido: string;
    score: number;
    titulo: string;
    fuente: string;
  }>;
}

export interface DocumentoItem {
  documento_id: number;
  titulo: string;
  fuente: string;
  tipo_documento: string;
  estado: string;
  nombre_archivo_original?: string;
  extension_archivo?: string;
  cantidad_fragmentos: number;
  fecha_creacion?: string;
}

export interface DocumentoDetalle {
  documento_id: number;
  titulo: string;
  fuente: string;
  tipo_documento: string;
  estado: string;
  nombre_archivo_original?: string;
  extension_archivo?: string;
  cantidad_paginas?: number;
  cantidad_fragmentos: number;
  fragmentos: Array<{
    id_fragmento: number;
    numero_orden: number;
    contenido: string;
    cantidad_caracteres: number;
  }>;
}

export interface HealthStatus {
  status: string;
  sessionmaker: boolean;
  proveedor_embeddings: boolean;
  proveedor_llm: boolean;
}

export interface EjemploArchivos {
  archivos: string[];
  ruta_base: string;
}

export interface IngestaResultado {
  status: string;
  resultado: {
    documento_id: number;
    titulo: string;
    cantidad_fragmentos: number;
    estado: string;
    fuente: string;
    mensaje: string;
  };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  health: () => request<HealthStatus>("/health"),

  consultar: (consulta: string, limite = 10) =>
    request<ConsultaResult>("/consulta", {
      method: "POST",
      body: JSON.stringify({ consulta, limite }),
    }),

  consultarConGeneracion: (consulta: string, limite = 5) =>
    request<GeneracionResult>("/consultar-con-generacion", {
      method: "POST",
      body: JSON.stringify({ consulta, limite }),
    }),

  listarDocumentos: () => request<DocumentoItem[]>("/documentos"),

  obtenerDocumento: (id: number) =>
    request<DocumentoDetalle>(`/documento/${id}`),

  eliminarDocumento: (id: number) =>
    request<{ status: string; mensaje: string }>(`/documento/${id}`, {
      method: "DELETE",
    }),

  cargarContenido: (
    titulo: string,
    contenido: string,
    fuente = "frontend-poc",
    tipo_documento = "general"
  ) =>
    request<IngestaResultado>("/cargar-contenido", {
      method: "POST",
      body: JSON.stringify({ titulo, contenido, fuente, tipo_documento }),
    }),

  ingestarArchivo: (
    ruta_archivo: string,
    fuente = "archivo-local",
    tipo_documento = "general"
  ) =>
    request<IngestaResultado>("/ingestar-archivo", {
      method: "POST",
      body: JSON.stringify({ ruta_archivo, fuente, tipo_documento }),
    }),

  documentosEjemplo: () => request<EjemploArchivos>("/documentos-ejemplo"),
};