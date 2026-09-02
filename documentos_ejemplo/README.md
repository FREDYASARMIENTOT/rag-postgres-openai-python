# Documentos de Ejemplo — RAG Institucional

Documentos de prueba multiformato para validar el pipeline de ingesta RAG
contra PostgreSQL Azure + Azure AI Foundry.

## Estructura

```
documentos_ejemplo/
├── README.md                 # Este archivo
├── generar_pdf_prueba.py     # Script para regenerar PDF
├── md/
│   └── facultades_ur_prueba.md    # Markdown (facultades UR)
├── txt/
│   └── facultades_ur_prueba.txt   # Texto plano (facultades UR)
├── pdf/
│   └── facultades_ur_prueba.pdf   # PDF generado con PyMuPDF
├── docx/
│   └── (pendiente)
└── pptx/
    └── (pendiente)
```

## Contenido

Los documentos contienen información institucional de la Universidad del
Rosario: descripción de sus facultades, escuelas y programas académicos.

## Regenerar PDF

```bash
cd documentos_ejemplo
python generar_pdf_prueba.py
```

## Uso

Estos archivos se procesan con `servicio_ingesta.py` que utiliza
`extractor_documentos.py` para extraer texto y `fragmentador_documentos.py`
para fragmentar. El flujo E2E valida:

1. Extracción de texto multiformato
2. Fragmentación automática
3. Generación de embeddings (text-embedding-3-large, 3072 dims)
4. Almacenamiento con deduplicación SHA-256
5. Retrieval semántico y generación con GPT-5.6 Luna