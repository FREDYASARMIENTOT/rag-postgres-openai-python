# Decisión de LLM — Foundry (Azure AI Studio)

**Documento:** DECISION-LLM-FOUNDRY.md  
**Versión:** 2.0 — Fase Foundry  
**Fecha:** 2026-01-09  
**Status:** ✅ IMPLEMENTACIÓN COMPLETADA — Deployments verificados en Azure

---

## 1. Objetivo

Documentar la decisión de crear el deployment dedicado `ur-rag-gpt-5-6-luna`
(modelo `gpt-5.6-luna`) como LLM principal del RAG Institucional,
sustituyendo el deployment actual `sii-supervisor-gpt-4o-mini` (gpt-4o-mini).

---

## 2. Contexto

Se optó por un **deployment dedicado** dentro del recurso Foundry existente
(Modelo-IA-UR) en lugar de reutilizar `ur-dedep-gpt-5.6-sol`, para:

- **Aislamiento de cuota**: El RAG no competirá con otros proyectos.
- **Previsibilidad**: Capacidad TPM configurable y controlable.
- **Idempotencia**: Script `deploy-foundry-rag-institucional.ps1` puede
  ejecutarse múltiples veces sin modificar deployments existentes.

### Recursos utilizados

| Propiedad | Valor |
|-----------|-------|
| Proyecto Foundry | `Proyecto-IA-UR` |
| Recurso AI | `Modelo-IA-UR` (Cognitive Services S0) |
| Grupo | `RG-Datamining-SII2.0-Dev` |
| Región | East US 2 |

---

## 3. Modelos Comparados

| Aspecto | gpt-4o-mini (legacy) | gpt-5.6-luna (nuevo) |
|---------|----------------------|----------------------|
| Proveedor | Azure OpenAI | Foundry (Modelo-IA-UR) |
| Deployment | `sii-supervisor-gpt-4o-mini` | `ur-rag-gpt-5-6-luna` |
| Generación | 4a generación | 5a generación |
| Capacidad | Compartida | Dedicada (10,000 TPM) |
| Costo estimado | Bajo | Medio/alto |
| Disponibilidad | ✅ Existente | ✅ Creado por script |
| Cuota | Compartida | Aislada |

---

## 4. Decisión

**DECISIÓN: Crear deployment dedicado `ur-rag-gpt-5-6-luna` (gpt-5.6-luna)**

Justificación:
1. **Aislamiento de cuota** — Evita impactar a otros proyectos que usan
   `ur-dedep-gpt-5.6-sol`.
2. **Modelo potente** — gpt-5.6-luna es de 5a generación, superior a
   gpt-4o-mini.
3. **Capacidad configurable** — 10,000 TPM por defecto, ajustable vía
   `-LlmTpmCapacity`.
4. **Mismo recurso** — Modelo-IA-UR, sin necesidad de otro servicio Azure.
5. **Automatizado** — Script idempotente `deploy-foundry-rag-institucional.ps1`.

---

## 5. Script de Deployment

```powershell
pwsh ./deploy-foundry-rag-institucional.ps1 `
    -ResourceGroupName "RG-Datamining-SII2.0-Dev" `
    -LlmDeploymentName "ur-rag-gpt-5-6-luna" `
    -LlmModelName "gpt-5.6-luna" `
    -LlmModelVersion "2026-07-09" `
    -LlmTpmCapacity 10000
```

Ver `docs/operaciones/` para detalles de ejecución.

---

## 6. Protección del Deployment Legacy

El deployment `sii-supervisor-gpt-4o-mini` **NO se modifica, elimina ni
reutiliza**. El script `deploy-foundry-rag-institucional.ps1` verifica
explícitamente que permanezca intacto.

---

## 7. Configuración

```bash
OPENAI_CHAT_HOST=foundry
FOUNDRY_CHAT_DEPLOYMENT=ur-rag-gpt-5-6-luna
FOUNDRY_CHAT_MODEL=gpt-5.6-luna
```

---

## 8. Estado de Implementación

| Operación | Estado | Fecha |
|-----------|--------|-------|
| Deployment `ur-rag-gpt-5-6-luna` (gpt-5.6-luna) creado | ✅ COMPLETADO — Succeeded | 2026-01-09 |
| Endpoint Foundry confirmado | ✅ `https://modelo-ia-ur.cognitiveservices.azure.com/` | 2026-01-09 |
| Legacy `sii-supervisor-gpt-4o-mini` verificado intacto | ✅ CONFIRMADO | 2026-01-09 |
| Verificar cuota y rate limits | ⏳ PENDIENTE (monitoreo continuo) | — |
| Validar respuesta gpt-5.6-luna en RAG | ⏳ PENDIENTE (requiere conexión real) | — |
| Ajustar TPM capacity si necesario | ⏳ PENDIENTE (según monitoreo) | — |

---

## 9. Referencias

- [Integración Foundry](../arquitectura/FOUNDRY-INTEGRATION.md)
- [Script de deployment](../operaciones/../deploy-foundry-rag-institucional.ps1)
- [Decisión de Embeddings](DECISION-EMBEDDINGS.md)
- [Arquitectura del RAG](../arquitectura/ARCHITECTURA-RAG.md)
- .env.sample (variables FOUNDRY_CHAT_*)

---

**Documento:** DECISION-LLM-FOUNDRY.md  
**Versión:** 2.0 | **Fecha:** 2026-01-09 | **Status:** ✅ DEPLOYMENT DEDICADO