#!/bin/bash
# =============================================================================
# VALIDACIÓN DE PRERREQUISITOS AZURE PARA DESPLIEGUE DEL RAG INSTITUCIONAL
# =============================================================================
# Modo: DRY-RUN (solo validación, NO modifica recursos)
# 
# USO:
#   ./scripts/validate-azure-prequisites.sh          # Validación general
#   ./scripts/validate-azure-prequisites.sh --verbose # Salida detallada
#
# REQUISITOS:
#   - Azure CLI instalado y autenticado (az login / azd auth login)
#   - Suscripción: Universidad del Rosario - DevOps
#   - Permisos de lectura en RG-Datamining-SII2.0-Dev
#
# NO ejecuta:
#   - Creación/modificación de recursos
#   - Habilitación de pgvector
#   - Despliegues de aplicaciones
# =============================================================================
set -euo pipefail

SUBSCRIPTION="Universidad del Rosario - DevOps"
RESOURCE_GROUP="RG-Datamining-SII2.0-Dev"
POSTGRES_SERVER="supersetdev"
AI_SERVICES_NAME="Modelo-IA-UR"
VERBOSE=false
for arg in "$@"; do [ "$arg" = "--verbose" ] && VERBOSE=true; done

EXIT_CODE=0
info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*" >&2; }
error() { echo "[ERROR] $*" >&2; }
pass() { echo "[PASS] $*"; }
fail() { echo "[FAIL] $*" >&2; EXIT_CODE=1; }
echo "=========================================="
echo "VALIDACIÓN DE PRERREQUISITOS AZURE - RAG"
echo "=========================================="
echo "Modo: SOLO LECTURA (dry-run)"
echo ""

# 1. VERIFICAR AUTENTICACIÓN
info "1. Verificando autenticación Azure..."
if az account show &>/dev/null; then
    ACCOUNT_NAME=$(az account show --query name -o tsv)
    pass "Autenticado en: $ACCOUNT_NAME"
else
    fail "No autenticado. Ejecute: az login o azd auth login"
fi

# 2. VERIFICAR SUSCRIPCIÓN
info "2. Verificando suscripción target..."
CURRENT_SUB=$(az account show --query name -o tsv 2>/dev/null)
if echo "$CURRENT_SUB" | grep -qi "universidad del rosario"; then
    pass "Suscripción: $CURRENT_SUB"
else
    fail "Suscripción actual: $CURRENT_SUB (se esperaba: 'Universidad del Rosario - DevOps')"
fi
# 3. VERIFICAR GRUPO DE RECURSOS
info "3. Verificando Resource Group..."
if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    RG_LOCATION=$(az group show --name "$RESOURCE_GROUP" --query location -o tsv)
    pass "Resource Group '$RESOURCE_GROUP' encontrado en: $RG_LOCATION"
else
    fail "Resource Group '$RESOURCE_GROUP' NO encontrado"
fi

# 4. VERIFICAR POSTGRESQL
info "4. Verificando PostgreSQL Flexible Server '$POSTGRES_SERVER'..."
if az postgres flexible-server show -g "$RESOURCE_GROUP" -n "$POSTGRES_SERVER" &>/dev/null; then
    PG_STATE=$(az postgres flexible-server show -g "$RESOURCE_GROUP" -n "$POSTGRES_SERVER" --query state -o tsv)
    PG_VERSION=$(az postgres flexible-server show -g "$RESOURCE_GROUP" -n "$POSTGRES_SERVER" --query version -o tsv)
    PG_SKU=$(az postgres flexible-server show -g "$RESOURCE_GROUP" -n "$POSTGRES_SERVER" --query sku.name -o tsv)
    PG_STORAGE=$(az postgres flexible-server show -g "$RESOURCE_GROUP" -n "$POSTGRES_SERVER" --query storage.storageSizeGb -o tsv)
    pass "PostgreSQL '$POSTGRES_SERVER': estado=$PG_STATE, PG$PG_VERSION, $PG_SKU, ${PG_STORAGE}GB"

    # Verificar extensiones
    info "  Verificando pgvector en azure.extensions..."
    PG_EXT=$(az postgres flexible-server parameter show -g "$RESOURCE_GROUP" --server-name "$POSTGRES_SERVER" --name azure.extensions -o tsv 2>/dev/null | tr ',' '\n' | grep -i vector || echo "")
    if [ -z "$PG_EXT" ]; then
        warn "  pgvector NO está habilitado en azure.extensions"
        warn "  Para habilitar: az postgres flexible-server parameter set ... --name azure.extensions --value vector"
    else
        pass "  pgvector disponible en azure.extensions"
    fi

    # Listar bases de datos
    info "  Bases de datos existentes:"
    az postgres flexible-server db list -g "$RESOURCE_GROUP" --server-name "$POSTGRES_SERVER" --query "[].name" -o tsv 2>/dev/null | while read -r db; do
        [ "$db" = "superset" ] && warn "    $db (INTOCABLE - Superset)" && continue
        [ "$db" = "rag_institucional" ] && pass "    $db (EXISTE - RAG)" && continue
        info "    $db"
    done
else
    fail "PostgreSQL '$POSTGRES_SERVER' NO encontrado"
fi
# 5. VERIFICAR MODELO-IA-UR
info "5. Verificando Azure AI Services '$AI_SERVICES_NAME'..."
if az cognitiveservices account show -g "$RESOURCE_GROUP" -n "$AI_SERVICES_NAME" &>/dev/null; then
    AI_SKU=$(az cognitiveservices account show -g "$RESOURCE_GROUP" -n "$AI_SERVICES_NAME" --query sku.name -o tsv)
    AI_KIND=$(az cognitiveservices account show -g "$RESOURCE_GROUP" -n "$AI_SERVICES_NAME" --query kind -o tsv)
    AI_LOCATION=$(az cognitiveservices account show -g "$RESOURCE_GROUP" -n "$AI_SERVICES_NAME" --query location -o tsv)
    pass "Modelo-IA-UR: kind=$AI_KIND, SKU=$AI_SKU, región=$AI_LOCATION"

    AI_ENDPOINT=$(az cognitiveservices account show -g "$RESOURCE_GROUP" -n "$AI_SERVICES_NAME" --query properties.endpoint -o tsv 2>/dev/null)
    [ -n "$AI_ENDPOINT" ] && pass "  Endpoint: $AI_ENDPOINT" || warn "  Endpoint NO disponible"

    # Listar deployments (si existe el subcomando)
    info "  Deployments de modelo:"
    DEPLOYMENTS=$(az cognitiveservices account deployment list -g "$RESOURCE_GROUP" -n "$AI_SERVICES_NAME" --query "[].{n:name, m:properties.model.name}" -o tsv 2>/dev/null || echo "")
    [ -z "$DEPLOYMENTS" ] && warn "    (Modelo-IA-UR puede ser AI Services multiservicio, no OpenAI dedicado)" || echo "$DEPLOYMENTS"
else
    fail "Modelo-IA-UR NO encontrado"
fi

# 6. VERIFICAR RECURSOS DE MONITOREO
info "6. Verificando Log Analytics reutilizables..."
LA_COUNT=$(az monitor log-analytics workspace list -g "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
[ "$LA_COUNT" -gt 0 ] && pass "Existen $LA_COUNT workspace(s) Log Analytics" || info "No hay Log Analytics en el RG"

info "7. Verificando Application Insights reutilizables..."
AI_COUNT=$(az monitor app-insights component list -g "$RESOURCE_GROUP" --query "length(@)" -o tsv 2>/dev/null || echo 0)
[ "$AI_COUNT" -gt 0 ] && pass "Existen $AI_COUNT instancia(s) App Insights" || info "No hay App Insights en el RG"

# RESUMEN
echo ""
echo "=========================================="
echo "RESUMEN"
echo "=========================================="
[ "$EXIT_CODE" -eq 0 ] && echo "✅ TODAS LAS VALIDACIONES PASARON" || echo "❌ ALGUNAS VALIDACIONES FALLARON"
echo ""
echo "PRÓXIMOS PASOS (requieren aprobación):"
echo "  1. Habilitar pgvector en supersetdev"
echo "  2. Crear BD rag_institucional"
echo "  3. Verificar/crear deployment de embeddings en Modelo-IA-UR"
echo "  4. Desplegar Container App via azd up"
echo ""
echo "NO ejecutar todavía: azd up, CREATE EXTENSION vector, modificar BD superset"
echo ""
exit "$EXIT_CODE"