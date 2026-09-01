# Guía de Reutilización de Recursos Azure — Bicep

**Archivo:** REUTILIZACION-BICEP.md  
**Propósito:** Documentar cómo modificar `main.bicep` para reutilizar recursos existentes
en lugar de crear nuevos.

---

## 1. Principio

El template Bicep actual (`main.bicep`) crea recursos nuevos por defecto.
Para el RAG Institucional, debemos **reutilizar**:

1. **PostgreSQL Flexible Server** → `supersetdev` (East US 2, PG16, B1ms)
2. **Azure AI Services** → `Modelo-IA-UR` (multiservicio, S0)
3. **Log Analytics** → workspaces existentes en RG-Datamining-SII2.0-Dev
4. **Application Insights** → instancias existentes

---

## 2. Modificaciones Necesarias

### 2.1 PostgreSQL: DE desplegar A reutilizar

**Actual (despliega nuevo):**
```bicep
module postgres 'core/database/flexibleserver.bicep' = {
  name: 'postgres'
  params: { ... }
}
```

**Objetivo (reutilizar):**
```bicep
@description('Nombre del PostgreSQL Flexible Server existente a reutilizar')
param existingPostgresServerName string = 'supersetdev'

@description('Nombre de la base de datos a crear en el servidor existente')
param ragDatabaseName string = 'rag_institucional'

// NO crear el servidor, solo validar que existe (en script de validación)
```

### 2.2 Azure AI: DE desplegar A reutilizar

**Actual (despliega nuevo):**
```bicep
module openai 'core/ai/cognitiveservices.bicep' = {
  name: 'openai'
  params: { ... }
}
```

**Objetivo (referenciar existente):**
```bicep
@description('Nombre del Azure AI Services existente a reutilizar')
param existingAIServiceName string = 'Modelo-IA-UR'

// Obtener propiedades del recurso existente
resource existingAI 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: existingAIServiceName
}
```

### 2.3 Log Analytics: Reutilizar existente

```bicep
@description('Nombre de un Log Analytics workspace existente')
param existingLogAnalyticsName string = ''

resource existingLogAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: existingLogAnalyticsName
}
```

### 2.4 Application Insights: Reutilizar existente

```bicep
@description('Nombre de un Application Insights existente')
param existingAppInsightsName string = ''
```

---

## 3. Parámetros a agregar en main.parameters.json

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "existingPostgresServerName": {
      "value": "supersetdev"
    },
    "ragDatabaseName": {
      "value": "rag_institucional"
    },
    "existingAIServiceName": {
      "value": "Modelo-IA-UR"
    },
    "existingLogAnalyticsName": {
      "value": ""
    },
    "existingAppInsightsName": {
      "value": ""
    }
  }
}
```

---

## 4. Flujo de Validación

1. **Ejecutar** `scripts/validate-azure-prequisites.sh` (dry-run).
2. **Verificar** que todos los recursos existentes están disponibles.
3. **Revisar** las modificaciones a main.bicep propuestas aquí.
4. **Aprobar** antes de ejecutar `azd up`.

---

## 5. Riesgos

- Si no se referencia correctamente el recurso existente, `azd up` fallará.
- El template debe distinguir entre "crear nuevo" y "referenciar existente".
- Managed Identity del Container App debe tener acceso al PostgreSQL existente.

---

**Documento:** REUTILIZACION-BICEP.md  
**Fecha:** 2026-01-09 | **Status:** ⏳ PENDIENTE DE REVISIÓN