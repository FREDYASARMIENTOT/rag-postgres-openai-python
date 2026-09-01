#Requires -Version 7.0

<#
===============================================================================
PROYECTO
  RAG Institucional - Universidad del Rosario

OBJETIVO
  Crear DOS deployments independientes dentro del recurso Azure AI/F​oundry
  EXISTENTE:

    1. ur-rag-gpt-5-6-luna
       Modelo : gpt-5.6-luna
       Uso    : LLM / generación / RAG

    2. ur-rag-embedding-3-large
       Modelo : text-embedding-3-large
       Uso    : embeddings / pgvector

RECURSOS EXISTENTES
  Foundry Project : Proyecto-IA-UR
  AI Resource     : Modelo-IA-UR

REGLAS DE SEGURIDAD
  - NO crear un nuevo Azure AI Services.
  - NO crear un nuevo proyecto Foundry.
  - NO modificar sii-supervisor-gpt-4o-mini.
  - NO eliminar deployments.
  - NO modificar PostgreSQL.
  - NO almacenar API keys.
  - NO almacenar passwords.
  - Usar Azure CLI + Azure Identity.
  - Registrar todas las operaciones.
  - Nunca imprimir secretos.
  - Si una operación falla, detener la operación correspondiente.
  - Los deployments creados antes del fallo se conservan.
  - No ejecutar rollback destructivo.

IDEMPOTENCIA
  - Si un deployment ya existe, NO se modifica.
  - Si un deployment no existe, se crea.
  - El script puede ejecutarse nuevamente sin modificar deployments existentes.

CUOTA
  Cada deployment recibe una capacidad independiente configurada mediante
  -LlmTpmCapacity y -EmbeddingTpmCapacity.

IMPORTANTE
  Azure administra cuota según sus ámbitos de suscripción/región/modelo/tipo.
  Deployments independientes permiten configurar capacidades independientes,
  pero NO constituyen aislamiento físico de cuota.

NOTA SOBRE EMBEDDING DIMENSIONS
  -EmbeddingDimensions NO se envía a "az cognitiveservices account
  deployment create", porque la dimensión del vector no es una propiedad
  configurable mediante ese comando de deployment.
  
  El valor se conserva como configuración esperada de la aplicación RAG.
  Debe coincidir con la dimensión utilizada por el pipeline de embeddings
  y con el esquema de pgvector.

EJECUCIÓN

  pwsh ./deploy-foundry-rag-institucional.ps1

EJEMPLO:

  pwsh ./deploy-foundry-rag-institucional.ps1 `
      -ResourceGroupName "MI-RESOURCE-GROUP" `
      -SubscriptionId "SUBSCRIPTION-ID" `
      -LlmTpmCapacity 10000 `
      -EmbeddingTpmCapacity 10000

MODO NO INTERACTIVO:

  pwsh ./deploy-foundry-rag-institucional.ps1 `
      -ResourceGroupName "MI-RESOURCE-GROUP" `
      -Force

===============================================================================
#>

[CmdletBinding()]
param(

    # -------------------------------------------------------------------------
    # Azure context
    # -------------------------------------------------------------------------

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$ResourceGroupName = "",

    [Parameter()]
    [string]$SubscriptionId = "",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$ExpectedTenantId = "ae525757-89ba-4d30-a2f7-49796ef8c604",

    # -------------------------------------------------------------------------
    # Foundry / Azure AI
    # -------------------------------------------------------------------------

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$FoundryProjectName = "Proyecto-IA-UR",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$AiResourceName = "Modelo-IA-UR",

    # -------------------------------------------------------------------------
    # LLM deployment
    # -------------------------------------------------------------------------

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$LlmDeploymentName = "ur-rag-gpt-5-6-luna",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$LlmModelName = "gpt-5.6-luna",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$LlmModelVersion = "2026-07-09",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$LlmModelFormat = "OpenAI",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$LlmSkuName = "GlobalStandard",

    [Parameter()]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$LlmTpmCapacity = 10000,

    # -------------------------------------------------------------------------
    # Embedding deployment
    # -------------------------------------------------------------------------

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$EmbeddingDeploymentName = "ur-rag-embedding-3-large",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$EmbeddingModelName = "text-embedding-3-large",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$EmbeddingModelVersion = "1",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$EmbeddingModelFormat = "OpenAI",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$EmbeddingSkuName = "Standard",

    [Parameter()]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$EmbeddingTpmCapacity = 10000,

    # Dimensión esperada por la aplicación RAG / pgvector.
    # NO se envía al comando de deployment Azure CLI.
    [Parameter()]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$EmbeddingDimensions = 1024,

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$LogDirectory = ".\logs",

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    [Parameter()]
    [switch]$SkipAzureLoginCheck,

    [Parameter()]
    [switch]$Force
)

# =============================================================================
# CONFIGURACIÓN GLOBAL
# =============================================================================

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$script:ScriptStartTime = Get-Date
$script:Timestamp = $script:ScriptStartTime.ToString("yyyyMMdd-HHmmss")

$script:ResourceGroupNameResolved = $false
$script:AzureAccount = $null
$script:AiResource = $null
$script:ExistingDeployments = @()
$script:LegacyDeploymentExists = $false
$script:TranscriptStarted = $false

$script:OperationResults = [System.Collections.Generic.List[object]]::new()

# =============================================================================
# DIRECTORIOS Y ARCHIVOS
# =============================================================================

if (-not (Test-Path -LiteralPath $LogDirectory)) {

    New-Item `
        -ItemType Directory `
        -Path $LogDirectory `
        -Force |
        Out-Null
}

$script:LogFile = Join-Path `
    -Path $LogDirectory `
    -ChildPath "foundry-rag-deployment-$Timestamp.log"

$script:TranscriptFile = Join-Path `
    -Path $LogDirectory `
    -ChildPath "foundry-rag-transcript-$Timestamp.log"

$script:StateFile = Join-Path `
    -Path $LogDirectory `
    -ChildPath "foundry-rag-deployment-state-$Timestamp.json"

# =============================================================================
# UTILIDADES
# =============================================================================

function Write-Log {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [AllowEmptyString()]
        [string]$Message,

        [ValidateSet(
            "INFO",
            "WARN",
            "ERROR",
            "SUCCESS",
            "STEP"
        )]
        [string]$Level = "INFO"
    )

    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    if ($Level -eq "STEP") {

        $separator = "=" * 78

        $lines = @(
            ""
            $separator
            $Message
            $separator
        )
    }
    else {

        $lines = @(
            "[$now] [$Level] $Message"
        )
    }

    foreach ($line in $lines) {

        Add-Content `
            -LiteralPath $script:LogFile `
            -Value $line `
            -Encoding UTF8
    }

    switch ($Level) {

        "ERROR" {
            foreach ($line in $lines) {
                Write-Host $line -ForegroundColor Red
            }
        }

        "WARN" {
            foreach ($line in $lines) {
                Write-Host $line -ForegroundColor Yellow
            }
        }

        "SUCCESS" {
            foreach ($line in $lines) {
                Write-Host $line -ForegroundColor Green
            }
        }

        "STEP" {
            foreach ($line in $lines) {
                Write-Host $line -ForegroundColor Cyan
            }
        }

        default {
            foreach ($line in $lines) {
                Write-Host $line
            }
        }
    }
}

function Write-CommandLog {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$CommandName,

        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    # IMPORTANTE:
    # No se registran tokens, passwords ni API keys.
    $safeArguments = $Arguments -join " "

    Write-Log `
        -Message "Azure CLI -> $CommandName $safeArguments" `
        -Level "INFO"
}

function Add-OperationResult {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Operation,

        [Parameter(Mandatory)]
        [string]$Status,

        [string]$Deployment = "",

        [string]$Message = ""
    )

    $script:OperationResults.Add(
        [PSCustomObject]@{
            Timestamp  = (Get-Date).ToString("s")
            Operation  = $Operation
            Status     = $Status
            Deployment = $Deployment
            Message    = $Message
        }
    )
}

function Test-StringNotEmpty {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Value,

        [Parameter(Mandatory)]
        [string]$Name
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {

        throw "$Name no puede estar vacío."
    }
}

# =============================================================================
# EJECUCIÓN SEGURA DE AZ CLI
# =============================================================================

function Invoke-AzCli {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$Operation,

        [switch]$AllowFailure
    )

    Write-CommandLog `
        -CommandName "az" `
        -Arguments $Arguments

    $output = @()

    try {

        $output = & az @Arguments 2>&1

        $exitCode = $LASTEXITCODE

        foreach ($line in $output) {

            Add-Content `
                -LiteralPath $script:LogFile `
                -Value "[AZCLI] $line" `
                -Encoding UTF8
        }

        if ($exitCode -ne 0) {

            $safeOutput = ($output -join "`n")

            if ($AllowFailure) {

                Write-Log `
                    -Message "$Operation devolvió exit code $exitCode." `
                    -Level "WARN"

                return [PSCustomObject]@{
                    Success  = $false
                    ExitCode = $exitCode
                    Output   = $safeOutput
                }
            }

            throw @"
Azure CLI error.

Operation:
$Operation

ExitCode:
$exitCode

Output:
$safeOutput
"@
        }

        return [PSCustomObject]@{
            Success  = $true
            ExitCode = 0
            Output   = ($output -join "`n")
        }
    }
    catch {

        if ($AllowFailure) {

            Write-Log `
                -Message "$Operation falló de forma controlada: $($_.Exception.Message)" `
                -Level "WARN"

            return [PSCustomObject]@{
                Success  = $false
                ExitCode = if ($null -ne $LASTEXITCODE) {
                    $LASTEXITCODE
                }
                else {
                    -1
                }
                Output = $_.Exception.Message
            }
        }

        Write-Log `
            -Message "$Operation FAILED: $($_.Exception.Message)" `
            -Level "ERROR"

        throw
    }
}

function Invoke-AzCliJson {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$Operation
    )

    $result = Invoke-AzCli `
        -Arguments $Arguments `
        -Operation $Operation

    if (-not $result.Success) {

        throw "$Operation falló."
    }

    if ([string]::IsNullOrWhiteSpace($result.Output)) {

        throw "$Operation no devolvió JSON."
    }

    try {

        return $result.Output | ConvertFrom-Json
    }
    catch {

        throw @"
No fue posible interpretar la respuesta JSON de Azure CLI.

Operación:
$Operation

Error:
$($_.Exception.Message)
"@
    }
}

# =============================================================================
# VALIDACIÓN DE HERRAMIENTAS
# =============================================================================

function Test-RequiredTools {

    Write-Log `
        -Message "VALIDACIÓN DE HERRAMIENTAS" `
        -Level "STEP"

    $azCommand = Get-Command az -ErrorAction SilentlyContinue

    if (-not $azCommand) {

        throw @"
Azure CLI no está instalado o no está disponible en PATH.

Instala Azure CLI y vuelve a ejecutar el script.
"@
    }

    $versionResult = Invoke-AzCli `
        -Arguments @(
            "version"
            "--output"
            "json"
        ) `
        -Operation "Validar versión de Azure CLI"

    if (-not $versionResult.Success) {

        throw "No fue posible ejecutar Azure CLI."
    }

    Write-Log `
        -Message "Azure CLI detectado correctamente." `
        -Level "SUCCESS"

    Add-OperationResult `
        -Operation "Azure CLI" `
        -Status "OK"
}

# =============================================================================
# AUTENTICACIÓN AZURE
# =============================================================================

function Test-AzureAuthentication {

    Write-Log `
        -Message "VALIDACIÓN DE AUTENTICACIÓN AZURE" `
        -Level "STEP"

    if ($SkipAzureLoginCheck) {

        Write-Log `
            -Message "Se omitió la validación explícita de Azure login." `
            -Level "WARN"

        Add-OperationResult `
            -Operation "Azure Authentication" `
            -Status "SKIPPED"

        return
    }

    $account = Invoke-AzCliJson `
        -Arguments @(
            "account"
            "show"
            "--output"
            "json"
        ) `
        -Operation "Obtener contexto Azure actual"

    if (-not $account) {

        throw "Azure CLI no devolvió información de la cuenta."
    }

    $script:AzureAccount = $account

    Write-Log `
        -Message "Tenant actual: $($account.tenantId)" `
        -Level "INFO"

    Write-Log `
        -Message "Suscripción actual: $($account.name) [$($account.id)]" `
        -Level "INFO"

    if ($account.tenantId -ne $ExpectedTenantId) {

        throw @"
TENANT INCORRECTO.

Tenant esperado:
$ExpectedTenantId

Tenant encontrado:
$($account.tenantId)

No se realizarán cambios.
"@
    }

    if (-not [string]::IsNullOrWhiteSpace($SubscriptionId)) {

        Write-Log `
            -Message "Seleccionando suscripción explícita." `
            -Level "INFO"

        Invoke-AzCli `
            -Arguments @(
                "account"
                "set"
                "--subscription"
                $SubscriptionId
            ) `
            -Operation "Seleccionar suscripción"

        $accountAfterSet = Invoke-AzCliJson `
            -Arguments @(
                "account"
                "show"
                "--output"
                "json"
            ) `
            -Operation "Validar suscripción seleccionada"

        if ($accountAfterSet.id -ne $SubscriptionId) {

            throw @"
La suscripción activa no coincide con SubscriptionId.

Esperada:
$SubscriptionId

Actual:
$($accountAfterSet.id)
"@
        }

        if ($accountAfterSet.tenantId -ne $ExpectedTenantId) {

            throw @"
La suscripción seleccionada pertenece a un tenant diferente.

Tenant esperado:
$ExpectedTenantId

Tenant encontrado:
$($accountAfterSet.tenantId)
"@
        }

        $script:AzureAccount = $accountAfterSet

        Write-Log `
            -Message "Suscripción seleccionada correctamente." `
            -Level "SUCCESS"
    }

    Add-OperationResult `
        -Operation "Azure Authentication" `
        -Status "OK"
}

# =============================================================================
# RESOLVER RESOURCE GROUP
# =============================================================================

function Resolve-ResourceGroup {

    Write-Log `
        -Message "RESOLUCIÓN DEL RESOURCE GROUP" `
        -Level "STEP"

    if (-not [string]::IsNullOrWhiteSpace($ResourceGroupName)) {

        Write-Log `
            -Message "Resource Group suministrado: $ResourceGroupName" `
            -Level "INFO"

        $script:ResourceGroupNameResolved = $true

        return
    }

    Write-Log `
        -Message "Resource Group no suministrado. Se resolverá exclusivamente para $AiResourceName." `
        -Level "WARN"

    $resourceGroup = Invoke-AzCli `
        -Arguments @(
            "resource"
            "show"
            "--name"
            $AiResourceName
            "--resource-type"
            "Microsoft.CognitiveServices/accounts"
            "--query"
            "resourceGroup"
            "--output"
            "tsv"
        ) `
        -Operation "Resolver Resource Group de $AiResourceName"

    $resolved = $resourceGroup.Output.Trim()

    if ([string]::IsNullOrWhiteSpace($resolved)) {

        throw @"
No fue posible resolver el Resource Group de:

$AiResourceName

Ejecuta nuevamente especificando:

-ResourceGroupName "NOMBRE_DEL_RESOURCE_GROUP"
"@
    }

    $script:ResourceGroupName = $resolved
    $script:ResourceGroupNameResolved = $true

    Write-Log `
        -Message "Resource Group resuelto: $ResourceGroupName" `
        -Level "SUCCESS"

    Add-OperationResult `
        -Operation "Resource Group resolution" `
        -Status "OK" `
        -Message $ResourceGroupName
}

# =============================================================================
# VALIDACIÓN DEL AI RESOURCE
# =============================================================================

function Test-AiResource {

    Write-Log `
        -Message "VALIDACIÓN DEL AI RESOURCE EXISTENTE" `
        -Level "STEP"

    $resource = Invoke-AzCliJson `
        -Arguments @(
            "cognitiveservices"
            "account"
            "show"
            "--name"
            $AiResourceName
            "--resource-group"
            $ResourceGroupName
            "--output"
            "json"
        ) `
        -Operation "Validar recurso $AiResourceName"

    if (-not $resource) {

        throw "No fue posible obtener $AiResourceName."
    }

    if ($resource.name -ne $AiResourceName) {

        throw @"
El recurso encontrado no coincide.

Esperado:
$AiResourceName

Encontrado:
$($resource.name)
"@
    }

    $script:AiResource = $resource

    Write-Log `
        -Message "Recurso confirmado: $($resource.name)" `
        -Level "SUCCESS"

    Write-Log `
        -Message "Tipo: $($resource.kind)" `
        -Level "INFO"

    Write-Log `
        -Message "Región: $($resource.location)" `
        -Level "INFO"

    Write-Log `
        -Message "SKU: $($resource.sku.name)" `
        -Level "INFO"

    Add-OperationResult `
        -Operation "AI Resource validation" `
        -Status "OK" `
        -Message $AiResourceName
}

# =============================================================================
# CARGAR DEPLOYMENTS EXISTENTES
# =============================================================================

function Get-ExistingDeployments {

    Write-Log `
        -Message "CARGANDO DEPLOYMENTS EXISTENTES" `
        -Level "STEP"

    $deployments = Invoke-AzCliJson `
        -Arguments @(
            "cognitiveservices"
            "account"
            "deployment"
            "list"
            "--name"
            $AiResourceName
            "--resource-group"
            $ResourceGroupName
            "--output"
            "json"
        ) `
        -Operation "Listar deployments existentes"

    if ($null -eq $deployments) {

        $script:ExistingDeployments = @()
    }
    else {

        $script:ExistingDeployments = @($deployments)
    }

    Write-Log `
        -Message "Deployments encontrados: $($script:ExistingDeployments.Count)" `
        -Level "INFO"

    foreach ($deployment in $script:ExistingDeployments) {

        Write-Log `
            -Message (
                "  - {0} | Estado={1} | Modelo={2} | Versión={3}" -f `
                $deployment.name,
                $deployment.properties.provisioningState,
                $deployment.properties.model.name,
                $deployment.properties.model.version
            ) `
            -Level "INFO"
    }

    Add-OperationResult `
        -Operation "Existing deployments discovery" `
        -Status "OK" `
        -Message "$($script:ExistingDeployments.Count) deployment(s)"
}

function Get-ExistingDeploymentByName {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$DeploymentName
    )

    $matches = @(
        $script:ExistingDeployments |
            Where-Object {
                $_.name -eq $DeploymentName
            }
    )

    if ($matches.Count -eq 0) {

        return $null
    }

    return $matches[0]
}

# =============================================================================
# PROTECCIÓN DEL DEPLOYMENT LEGACY
# =============================================================================

function Protect-LegacyDeployment {

    Write-Log `
        -Message "PROTECCIÓN DEL DEPLOYMENT LEGACY" `
        -Level "STEP"

    $legacyDeploymentName = "sii-supervisor-gpt-4o-mini"

    $legacy = Get-ExistingDeploymentByName `
        -DeploymentName $legacyDeploymentName

    if ($legacy) {

        $script:LegacyDeploymentExists = $true

        Write-Log `
            -Message "Deployment legacy detectado: $legacyDeploymentName" `
            -Level "SUCCESS"

        Write-Log `
            -Message "No será modificado, eliminado ni reutilizado." `
            -Level "SUCCESS"
    }
    else {

        $script:LegacyDeploymentExists = $false

        Write-Log `
            -Message "No se encontró $legacyDeploymentName. El script no lo creará." `
            -Level "WARN"
    }

    Add-OperationResult `
        -Operation "Legacy deployment protection" `
        -Status "PROTECTED" `
        -Deployment $legacyDeploymentName
}

# =============================================================================
# VALIDACIÓN DE NOMBRES Y CONFIGURACIÓN
# =============================================================================

function Test-DeploymentConfiguration {

    Write-Log `
        -Message "VALIDACIÓN DE CONFIGURACIÓN DE DEPLOYMENTS" `
        -Level "STEP"

    $legacyDeploymentName = "sii-supervisor-gpt-4o-mini"

    Test-StringNotEmpty `
        -Value $LlmDeploymentName `
        -Name "LlmDeploymentName"

    Test-StringNotEmpty `
        -Value $EmbeddingDeploymentName `
        -Name "EmbeddingDeploymentName"

    if ($LlmDeploymentName -eq $legacyDeploymentName) {

        throw @"
El deployment LLM no puede utilizar el nombre protegido:

$legacyDeploymentName
"@
    }

    if ($EmbeddingDeploymentName -eq $legacyDeploymentName) {

        throw @"
El deployment de embeddings no puede utilizar el nombre protegido:

$legacyDeploymentName
"@
    }

    if ($LlmDeploymentName -eq $EmbeddingDeploymentName) {

        throw @"
Los deployments LLM y Embedding deben tener nombres diferentes.
"@
    }

    if ($LlmTpmCapacity -le 0) {

        throw "LlmTpmCapacity debe ser mayor que cero."
    }

    if ($EmbeddingTpmCapacity -le 0) {

        throw "EmbeddingTpmCapacity debe ser mayor que cero."
    }

    if ($EmbeddingDimensions -ne 1024) {

        Write-Log `
            -Message (
                "EmbeddingDimensions=$EmbeddingDimensions. " +
                "El proyecto RAG actualmente está configurado para 1024."
            ) `
            -Level "WARN"
    }

    Write-Log `
        -Message "LLM Deployment       : $LlmDeploymentName" `
        -Level "INFO"

    Write-Log `
        -Message "LLM Model            : $LlmModelName" `
        -Level "INFO"

    Write-Log `
        -Message "LLM Version          : $LlmModelVersion" `
        -Level "INFO"

    Write-Log `
        -Message "LLM SKU              : $LlmSkuName" `
        -Level "INFO"

    Write-Log `
        -Message "LLM Capacity         : $LlmTpmCapacity" `
        -Level "INFO"

    Write-Log `
        -Message "Embedding Deployment : $EmbeddingDeploymentName" `
        -Level "INFO"

    Write-Log `
        -Message "Embedding Model      : $EmbeddingModelName" `
        -Level "INFO"

    Write-Log `
        -Message "Embedding Version    : $EmbeddingModelVersion" `
        -Level "INFO"

    Write-Log `
        -Message "Embedding SKU        : $EmbeddingSkuName" `
        -Level "INFO"

    Write-Log `
        -Message "Embedding Capacity   : $EmbeddingTpmCapacity" `
        -Level "INFO"

    Write-Log `
        -Message "Embedding Dimensions : $EmbeddingDimensions" `
        -Level "INFO"

    Add-OperationResult `
        -Operation "Deployment configuration validation" `
        -Status "OK"
}

# =============================================================================
# VALIDACIÓN DE MODELOS
# =============================================================================

function Test-ModelAvailability {

    Write-Log `
        -Message "VALIDACIÓN DE DISPONIBILIDAD DE MODELOS" `
        -Level "STEP"

    $models = Invoke-AzCliJson `
        -Arguments @(
            "cognitiveservices"
            "account"
            "list-models"
            "--name"
            $AiResourceName
            "--resource-group"
            $ResourceGroupName
            "--output"
            "json"
        ) `
        -Operation "Consultar catálogo de modelos de $AiResourceName"

    if (-not $models) {

        throw "El recurso $AiResourceName no devolvió catálogo de modelos."
    }

    $llmCandidates = @(
        $models |
            Where-Object {
                $_.name -eq $LlmModelName -and
                $_.version -eq $LlmModelVersion
            }
    )

    if ($llmCandidates.Count -eq 0) {

        throw @"
El modelo LLM solicitado NO aparece en el catálogo de $AiResourceName.

Modelo:
$LlmModelName

Versión:
$LlmModelVersion

NO se creará el deployment LLM.
"@
    }

    Write-Log `
        -Message "Modelo LLM confirmado: $LlmModelName / $LlmModelVersion" `
        -Level "SUCCESS"

    $embeddingCandidates = @(
        $models |
            Where-Object {
                $_.name -eq $EmbeddingModelName -and
                $_.version -eq $EmbeddingModelVersion
            }
    )

    if ($embeddingCandidates.Count -eq 0) {

        throw @"
El modelo de embeddings solicitado NO aparece en el catálogo de
$AiResourceName.

Modelo:
$EmbeddingModelName

Versión:
$EmbeddingModelVersion

NO se creará el deployment de embeddings.
"@
    }

    Write-Log `
        -Message "Modelo Embedding confirmado: $EmbeddingModelName / $EmbeddingModelVersion" `
        -Level "SUCCESS"

    Add-OperationResult `
        -Operation "Model availability" `
        -Status "OK"
}

# =============================================================================
# DETECTAR CONFLICTOS CON DEPLOYMENTS EXISTENTES
# =============================================================================

function Test-ExistingDeploymentCompatibility {

    Write-Log `
        -Message "VALIDACIÓN DE DEPLOYMENTS RAG EXISTENTES" `
        -Level "STEP"

    $targets = @(
        [PSCustomObject]@{
            Type       = "LLM"
            Name       = $LlmDeploymentName
            Model      = $LlmModelName
            Version    = $LlmModelVersion
            Format     = $LlmModelFormat
            Sku        = $LlmSkuName
            Capacity   = $LlmTpmCapacity
        },
        [PSCustomObject]@{
            Type       = "Embedding"
            Name       = $EmbeddingDeploymentName
            Model      = $EmbeddingModelName
            Version    = $EmbeddingModelVersion
            Format     = $EmbeddingModelFormat
            Sku        = $EmbeddingSkuName
            Capacity   = $EmbeddingTpmCapacity
        }
    )

    foreach ($target in $targets) {

        $existing = Get-ExistingDeploymentByName `
            -DeploymentName $target.Name

        if (-not $existing) {

            Write-Log `
                -Message "No existe $($target.Name). Se podrá crear." `
                -Level "INFO"

            continue
        }

        $existingModelName = $existing.properties.model.name
        $existingModelVersion = $existing.properties.model.version
        $existingModelFormat = $existing.properties.model.format

        Write-Log `
            -Message "Deployment existente detectado: $($target.Name)" `
            -Level "WARN"

        Write-Log `
            -Message "Modelo existente : $existingModelName" `
            -Level "INFO"

        Write-Log `
            -Message "Versión existente: $existingModelVersion" `
            -Level "INFO"

        Write-Log `
            -Message "Formato existente: $existingModelFormat" `
            -Level "INFO"

        if (
            $existingModelName -ne $target.Model -or
            $existingModelVersion -ne $target.Version -or
            $existingModelFormat -ne $target.Format
        ) {

            throw @"
CONFLICTO DE CONFIGURACIÓN.

El deployment ya existe pero apunta a una configuración diferente.

Deployment:
$($target.Name)

Configuración esperada:
  Modelo   : $($target.Model)
  Versión  : $($target.Version)
  Formato  : $($target.Format)

Configuración encontrada:
  Modelo   : $existingModelName
  Versión  : $existingModelVersion
  Formato  : $existingModelFormat

Por seguridad el script NO modificará el deployment existente.
"@
        }

        Write-Log `
            -Message "Configuración compatible. El deployment será conservado sin modificaciones." `
            -Level "SUCCESS"
    }

    Add-OperationResult `
        -Operation "Existing deployment compatibility" `
        -Status "OK"
}

# =============================================================================
# PLAN
# =============================================================================

function Show-DeploymentPlan {

    Write-Log `
        -Message "PLAN DE IMPLEMENTACIÓN - TODAVÍA NO SE HAN REALIZADO CAMBIOS" `
        -Level "STEP"

    Write-Host ""

    Write-Host "==================== CONTEXTO ====================" `
        -ForegroundColor Cyan

    Write-Host "Foundry Project : $FoundryProjectName"
    Write-Host "AI Resource     : $AiResourceName"
    Write-Host "Resource Group  : $ResourceGroupName"

    if ($script:AzureAccount) {

        Write-Host "Subscription    : $($script:AzureAccount.id)"
        Write-Host "Tenant          : $($script:AzureAccount.tenantId)"
    }

    Write-Host ""

    Write-Host "======================= LLM =======================" `
        -ForegroundColor Cyan

    Write-Host "Deployment      : $LlmDeploymentName"
    Write-Host "Model           : $LlmModelName"
    Write-Host "Version         : $LlmModelVersion"
    Write-Host "Format          : $LlmModelFormat"
    Write-Host "SKU             : $LlmSkuName"
    Write-Host "Capacity        : $LlmTpmCapacity"

    $existingLlm = Get-ExistingDeploymentByName `
        -DeploymentName $LlmDeploymentName

    if ($existingLlm) {

        Write-Host "Action          : CONSERVAR EXISTENTE" `
            -ForegroundColor Yellow
    }
    else {

        Write-Host "Action          : CREAR" `
            -ForegroundColor Green
    }

    Write-Host ""

    Write-Host "==================== EMBEDDINGS ===================" `
        -ForegroundColor Cyan

    Write-Host "Deployment      : $EmbeddingDeploymentName"
    Write-Host "Model           : $EmbeddingModelName"
    Write-Host "Version         : $EmbeddingModelVersion"
    Write-Host "Format          : $EmbeddingModelFormat"
    Write-Host "SKU             : $EmbeddingSkuName"
    Write-Host "Capacity        : $EmbeddingTpmCapacity"
    Write-Host "Vector dims     : $EmbeddingDimensions"
    Write-Host "Vector dims note : configuración de aplicación/pgvector"

    $existingEmbedding = Get-ExistingDeploymentByName `
        -DeploymentName $EmbeddingDeploymentName

    if ($existingEmbedding) {

        Write-Host "Action          : CONSERVAR EXISTENTE" `
            -ForegroundColor Yellow
    }
    else {

        Write-Host "Action          : CREAR" `
            -ForegroundColor Green
    }

    Write-Host ""

    Write-Host "================== PROTECCIÓN ====================" `
        -ForegroundColor Yellow

    Write-Host "Deployment protegido:"
    Write-Host "  sii-supervisor-gpt-4o-mini"

    Write-Host ""

    Write-Host "REGLAS:" -ForegroundColor Yellow
    Write-Host "  - No eliminar deployments."
    Write-Host "  - No modificar deployments existentes."
    Write-Host "  - No modificar PostgreSQL."
    Write-Host "  - No crear otro AI Resource."
    Write-Host "  - No crear otro Foundry Project."
    Write-Host "  - No ejecutar rollback destructivo."

    Write-Host ""

    if (-not $Force) {

        $confirmation = Read-Host `
            "Escriba CREAR-RAG para ejecutar el plan"

        if ($confirmation -ne "CREAR-RAG") {

            Write-Log `
                -Message "Ejecución cancelada por el usuario." `
                -Level "WARN"

            throw "Operación cancelada por el usuario."
        }
    }
    else {

        Write-Log `
            -Message "Modo -Force activo. Se omite confirmación interactiva." `
            -Level "WARN"
    }
}

# =============================================================================
# CREAR DEPLOYMENT GENÉRICO
# =============================================================================

function New-DeploymentIfMissing {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$DeploymentName,

        [Parameter(Mandatory)]
        [string]$ModelName,

        [Parameter(Mandatory)]
        [string]$ModelVersion,

        [Parameter(Mandatory)]
        [string]$ModelFormat,

        [Parameter(Mandatory)]
        [string]$SkuName,

        [Parameter(Mandatory)]
        [int]$SkuCapacity,

        [Parameter(Mandatory)]
        [string]$DeploymentType
    )

    Write-Log `
        -Message "DEPLOYMENT: $DeploymentType" `
        -Level "STEP"

    $existing = Get-ExistingDeploymentByName `
        -DeploymentName $DeploymentName

    if ($existing) {

        Write-Log `
            -Message "El deployment $DeploymentName ya existe." `
            -Level "WARN"

        Write-Log `
            -Message "No se realizará ninguna operación de modificación." `
            -Level "SUCCESS"

        Add-OperationResult `
            -Operation "$DeploymentType deployment" `
            -Status "EXISTING" `
            -Deployment $DeploymentName

        return $existing
    }

    Write-Log `
        -Message "Creando deployment $DeploymentName..." `
        -Level "INFO"

    $arguments = @(
        "cognitiveservices"
        "account"
        "deployment"
        "create"

        "--name"
        $AiResourceName

        "--resource-group"
        $ResourceGroupName

        "--deployment-name"
        $DeploymentName

        "--model-name"
        $ModelName

        "--model-version"
        $ModelVersion

        "--model-format"
        $ModelFormat

        "--sku-capacity"
        $SkuCapacity.ToString()

        "--sku-name"
        $SkuName

        "--output"
        "json"
    )

    try {

        $result = Invoke-AzCli `
            -Arguments $arguments `
            -Operation "Crear deployment $DeploymentName"

        if (-not $result.Success) {

            throw "Azure CLI no pudo crear $DeploymentName."
        }

        Write-Log `
            -Message "Solicitud de creación completada para $DeploymentName." `
            -Level "SUCCESS"

        Add-OperationResult `
            -Operation "$DeploymentType deployment" `
            -Status "CREATED" `
            -Deployment $DeploymentName

        # Actualizar caché local después de crear.
        $createdDeployment = $result.Output | ConvertFrom-Json

        return $createdDeployment
    }
    catch {

        Add-OperationResult `
            -Operation "$DeploymentType deployment" `
            -Status "FAILED" `
            -Deployment $DeploymentName `
            -Message $_.Exception.Message

        throw
    }
}

# =============================================================================
# ESPERAR DEPLOYMENT
# =============================================================================

function Wait-DeploymentReady {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$DeploymentName,

        [Parameter()]
        [ValidateRange(1, 3600)]
        [int]$PollingIntervalSeconds = 10,

        [Parameter()]
        [ValidateRange(1, 120)]
        [int]$MaxAttempts = 30
    )

    Write-Log `
        -Message "VALIDACIÓN DE PROVISIONING STATE: $DeploymentName" `
        -Level "STEP"

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {

        $deployment = Invoke-AzCliJson `
            -Arguments @(
                "cognitiveservices"
                "account"
                "deployment"
                "show"
                "--name"
                $AiResourceName
                "--resource-group"
                $ResourceGroupName
                "--deployment-name"
                $DeploymentName
                "--output"
                "json"
            ) `
            -Operation "Consultar estado de $DeploymentName"

        if (-not $deployment) {

            throw @"
No fue posible obtener información del deployment:

$DeploymentName
"@
        }

        $state = $deployment.properties.provisioningState

        Write-Log `
            -Message (
                "$DeploymentName -> provisioningState=$state " +
                "(intento $attempt/$MaxAttempts)"
            ) `
            -Level "INFO"

        switch ($state) {

            "Succeeded" {

                Write-Log `
                    -Message "$DeploymentName está listo." `
                    -Level "SUCCESS"

                return $deployment
            }

            "Failed" {

                throw @"
El deployment terminó en estado FAILED.

Deployment:
$DeploymentName

No se ejecutará rollback destructivo.

Revise:
$($script:LogFile)
"@
            }

            "Canceled" {

                throw @"
El deployment terminó en estado CANCELED.

Deployment:
$DeploymentName

No se ejecutará rollback destructivo.
"@
            }

            default {

                if ($attempt -lt $MaxAttempts) {

                    Start-Sleep `
                        -Seconds $PollingIntervalSeconds
                }
            }
        }
    }

    throw @"
TIMEOUT esperando provisioningState=Succeeded.

Deployment:
$DeploymentName

Intentos:
$MaxAttempts

Intervalo:
$PollingIntervalSeconds segundos

No se ejecutará rollback destructivo.
"@
}

# =============================================================================
# ACTUALIZAR CACHE DE DEPLOYMENTS
# =============================================================================

function Refresh-DeploymentCache {

    Write-Log `
        -Message "Actualizando inventario de deployments..." `
        -Level "INFO"

    $deployments = Invoke-AzCliJson `
        -Arguments @(
            "cognitiveservices"
            "account"
            "deployment"
            "list"
            "--name"
            $AiResourceName
            "--resource-group"
            $ResourceGroupName
            "--output"
            "json"
        ) `
        -Operation "Actualizar inventario de deployments"

    if ($null -eq $deployments) {

        $script:ExistingDeployments = @()
    }
    else {

        $script:ExistingDeployments = @($deployments)
    }
}

# =============================================================================
# VALIDACIÓN FINAL DE DEPLOYMENT
# =============================================================================

function Test-FinalDeployment {

    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$DeploymentName,

        [Parameter(Mandatory)]
        [string]$ExpectedModelName,

        [Parameter(Mandatory)]
        [string]$ExpectedModelVersion,

        [Parameter(Mandatory)]
        [string]$ExpectedModelFormat
    )

    $deployment = Get-ExistingDeploymentByName `
        -DeploymentName $DeploymentName

    if (-not $deployment) {

        throw @"
El deployment esperado NO existe después de la implementación.

Deployment:
$DeploymentName
"@
    }

    $state = $deployment.properties.provisioningState
    $modelName = $deployment.properties.model.name
    $modelVersion = $deployment.properties.model.version
    $modelFormat = $deployment.properties.model.format

    if ($state -ne "Succeeded") {

        throw @"
Deployment no está listo.

Deployment:
$DeploymentName

Estado:
$state
"@
    }

    if ($modelName -ne $ExpectedModelName) {

        throw @"
El modelo del deployment no coincide.

Deployment:
$DeploymentName

Esperado:
$ExpectedModelName

Encontrado:
$modelName
"@
    }

    if ($modelVersion -ne $ExpectedModelVersion) {

        throw @"
La versión del modelo no coincide.

Deployment:
$DeploymentName

Esperada:
$ExpectedModelVersion

Encontrada:
$modelVersion
"@
    }

    if ($modelFormat -ne $ExpectedModelFormat) {

        throw @"
El formato del modelo no coincide.

Deployment:
$DeploymentName

Esperado:
$ExpectedModelFormat

Encontrado:
$modelFormat
"@
    }

    Write-Log `
        -Message (
            "$DeploymentName VALIDADO | " +
            "State=$state | " +
            "Model=$modelName | " +
            "Version=$modelVersion | " +
            "Format=$modelFormat"
        ) `
        -Level "SUCCESS"

    return $deployment
}

# =============================================================================
# VALIDACIÓN FINAL COMPLETA
# =============================================================================

function Show-FinalDeployments {

    Write-Log `
        -Message "VALIDACIÓN FINAL DE DEPLOYMENTS" `
        -Level "STEP"

    Refresh-DeploymentCache

    $llm = Test-FinalDeployment `
        -DeploymentName $LlmDeploymentName `
        -ExpectedModelName $LlmModelName `
        -ExpectedModelVersion $LlmModelVersion `
        -ExpectedModelFormat $LlmModelFormat

    $embedding = Test-FinalDeployment `
        -DeploymentName $EmbeddingDeploymentName `
        -ExpectedModelName $EmbeddingModelName `
        -ExpectedModelVersion $EmbeddingModelVersion `
        -ExpectedModelFormat $EmbeddingModelFormat

    $legacy = Get-ExistingDeploymentByName `
        -DeploymentName "sii-supervisor-gpt-4o-mini"

    if ($legacy) {

        Write-Log `
            -Message "Deployment legacy sigue presente y no fue modificado." `
            -Level "SUCCESS"
    }

    $selected = @(
        $llm
        $embedding

        if ($legacy) {
            $legacy
        }
    )

    $finalState = [PSCustomObject]@{
        Timestamp = (Get-Date).ToString("o")

        Azure = [PSCustomObject]@{
            TenantId       = if ($script:AzureAccount) {
                $script:AzureAccount.tenantId
            }
            else {
                ""
            }

            SubscriptionId = if ($script:AzureAccount) {
                $script:AzureAccount.id
            }
            else {
                ""
            }

            ResourceGroup  = $ResourceGroupName
        }

        Foundry = [PSCustomObject]@{
            Project     = $FoundryProjectName
            AIResource  = $AiResourceName
        }

        RAG = [PSCustomObject]@{
            LLM = [PSCustomObject]@{
                Deployment = $LlmDeploymentName
                Model      = $LlmModelName
                Version    = $LlmModelVersion
                Format     = $LlmModelFormat
                SKU        = $LlmSkuName
                Capacity   = $LlmTpmCapacity
                State      = $llm.properties.provisioningState
            }

            Embedding = [PSCustomObject]@{
                Deployment = $EmbeddingDeploymentName
                Model      = $EmbeddingModelName
                Version    = $EmbeddingModelVersion
                Format     = $EmbeddingModelFormat
                SKU        = $EmbeddingSkuName
                Capacity   = $EmbeddingTpmCapacity

                # Propiedad de la aplicación RAG/pgvector.
                Dimensions = $EmbeddingDimensions

                State = $embedding.properties.provisioningState
            }
        }

        ProtectedDeployment = [PSCustomObject]@{
            Name   = "sii-supervisor-gpt-4o-mini"
            Exists = [bool]$legacy
        }

        DeploymentCount = $script:ExistingDeployments.Count
    }

    $finalState |
        ConvertTo-Json -Depth 20 |
        Set-Content `
            -LiteralPath $script:StateFile `
            -Encoding UTF8

    Write-Log `
        -Message "Estado final guardado en: $script:StateFile" `
        -Level "SUCCESS"

    return $selected
}

# =============================================================================
# RESUMEN FINAL
# =============================================================================

function Show-FinalSummary {

    Write-Log `
        -Message "RESUMEN FINAL" `
        -Level "STEP"

    Write-Host ""

    Write-Host "PROYECTO FOUND​RY" `
        -ForegroundColor Cyan

    Write-Host "  Proyecto       : $FoundryProjectName"
    Write-Host "  AI Resource    : $AiResourceName"
    Write-Host "  Resource Group : $ResourceGroupName"

    if ($script:AzureAccount) {

        Write-Host "  Subscription   : $($script:AzureAccount.id)"
        Write-Host "  Tenant         : $($script:AzureAccount.tenantId)"
    }

    Write-Host ""

    Write-Host "LLM" `
        -ForegroundColor Cyan

    Write-Host "  Deployment : $LlmDeploymentName"
    Write-Host "  Model      : $LlmModelName"
    Write-Host "  Version    : $LlmModelVersion"
    Write-Host "  SKU        : $LlmSkuName"
    Write-Host "  Capacity   : $LlmTpmCapacity TPM"

    Write-Host ""

    Write-Host "EMBEDDINGS" `
        -ForegroundColor Cyan

    Write-Host "  Deployment : $EmbeddingDeploymentName"
    Write-Host "  Model      : $EmbeddingModelName"
    Write-Host "  Version    : $EmbeddingModelVersion"
    Write-Host "  SKU        : $EmbeddingSkuName"
    Write-Host "  Capacity   : $EmbeddingTpmCapacity TPM"
    Write-Host "  Dimensions : $EmbeddingDimensions"

    Write-Host ""

    Write-Host "DEPLOYMENT PROTEGIDO" `
        -ForegroundColor Yellow

    Write-Host "  sii-supervisor-gpt-4o-mini"

    Write-Host ""

    Write-Host "RESULTADOS DE OPERACIONES" `
        -ForegroundColor Cyan

    if ($script:OperationResults.Count -gt 0) {

        $script:OperationResults |
            Format-Table `
                Timestamp,
                Operation,
                Status,
                Deployment,
                Message `
                -AutoSize
    }

    Write-Host ""

    Write-Host "ARCHIVOS DE AUDITORÍA" `
        -ForegroundColor Cyan

    Write-Host "  Log        : $script:LogFile"
    Write-Host "  Transcript : $script:TranscriptFile"
    Write-Host "  State JSON : $script:StateFile"

    Write-Host ""
}

# =============================================================================
# INICIO
# =============================================================================

try {

    # -------------------------------------------------------------------------
    # TRANSCRIPT
    # -------------------------------------------------------------------------

    try {

        Start-Transcript `
            -Path $script:TranscriptFile `
            -Force |
            Out-Null

        $script:TranscriptStarted = $true
    }
    catch {

        Write-Host `
            "WARN: No fue posible iniciar transcript: $($_.Exception.Message)" `
            -ForegroundColor Yellow
    }

    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------

    Write-Log `
        -Message "INICIO DEPLOYMENT FOUNDRY RAG INSTITUCIONAL" `
        -Level "STEP"

    Write-Log `
        -Message "Fecha/Hora: $script:ScriptStartTime" `
        -Level "INFO"

    Write-Log `
        -Message "Foundry Project: $FoundryProjectName" `
        -Level "INFO"

    Write-Log `
        -Message "AI Resource: $AiResourceName" `
        -Level "INFO"

    # -------------------------------------------------------------------------
    # PRECHECKS
    # -------------------------------------------------------------------------

    Test-RequiredTools

    Test-AzureAuthentication

    Resolve-ResourceGroup

    Test-AiResource

    Get-ExistingDeployments

    Test-DeploymentConfiguration

    Protect-LegacyDeployment

    Test-ExistingDeploymentCompatibility

    Test-ModelAvailability

    # -------------------------------------------------------------------------
    # PLAN
    # -------------------------------------------------------------------------

    Show-DeploymentPlan

    # -------------------------------------------------------------------------
    # DEPLOYMENT 1 - LLM
    # -------------------------------------------------------------------------

    Write-Log `
        -Message "IMPLEMENTACIÓN 1/2 - LLM" `
        -Level "STEP"

    $llmDeployment = New-DeploymentIfMissing `
        -DeploymentName $LlmDeploymentName `
        -ModelName $LlmModelName `
        -ModelVersion $LlmModelVersion `
        -ModelFormat $LlmModelFormat `
        -SkuName $LlmSkuName `
        -SkuCapacity $LlmTpmCapacity `
        -DeploymentType "LLM"

    # Esperar únicamente si acabamos de crear o si existe y aún está
    # provisioning.
    $llmState = $llmDeployment.properties.provisioningState

    if ($llmState -ne "Succeeded") {

        Wait-DeploymentReady `
            -DeploymentName $LlmDeploymentName
    }

    Refresh-DeploymentCache

    # -------------------------------------------------------------------------
    # DEPLOYMENT 2 - EMBEDDINGS
    # -------------------------------------------------------------------------

    Write-Log `
        -Message "IMPLEMENTACIÓN 2/2 - EMBEDDINGS" `
        -Level "STEP"

    $embeddingDeployment = New-DeploymentIfMissing `
        -DeploymentName $EmbeddingDeploymentName `
        -ModelName $EmbeddingModelName `
        -ModelVersion $EmbeddingModelVersion `
        -ModelFormat $EmbeddingModelFormat `
        -SkuName $EmbeddingSkuName `
        -SkuCapacity $EmbeddingTpmCapacity `
        -DeploymentType "Embedding"

    $embeddingState = $embeddingDeployment.properties.provisioningState

    if ($embeddingState -ne "Succeeded") {

        Wait-DeploymentReady `
            -DeploymentName $EmbeddingDeploymentName
    }

    # -------------------------------------------------------------------------
    # VALIDACIÓN FINAL
    # -------------------------------------------------------------------------

    Show-FinalDeployments | Out-Null

    Write-Log `
        -Message "TODAS LAS IMPLEMENTACIONES RAG TERMINARON CORRECTAMENTE." `
        -Level "SUCCESS"

    Show-FinalSummary

    exit 0
}
catch {

    # -------------------------------------------------------------------------
    # ERROR GLOBAL
    # -------------------------------------------------------------------------

    Write-Log `
        -Message "IMPLEMENTACIÓN INTERRUMPIDA" `
        -Level "ERROR"

    Write-Log `
        -Message $_.Exception.Message `
        -Level "ERROR"

    Write-Log `
        -Message "NO se ejecutará rollback destructivo." `
        -Level "WARN"

    Write-Log `
        -Message "Los deployments creados antes del fallo se conservarán." `
        -Level "WARN"

    Write-Log `
        -Message "Log principal: $script:LogFile" `
        -Level "ERROR"

    Write-Log `
        -Message "Transcript: $script:TranscriptFile" `
        -Level "ERROR"

    Write-Log `
        -Message "Estado JSON: $script:StateFile" `
        -Level "ERROR"

    # Intentar capturar el estado real después del fallo.
    try {

        if ($script:ResourceGroupNameResolved) {

            Refresh-DeploymentCache

            $failureState = [PSCustomObject]@{
                Timestamp = (Get-Date).ToString("o")
                Status    = "FAILED"

                Error = $_.Exception.Message

                Azure = [PSCustomObject]@{
                    TenantId = if ($script:AzureAccount) {
                        $script:AzureAccount.tenantId
                    }
                    else {
                        ""
                    }

                    SubscriptionId = if ($script:AzureAccount) {
                        $script:AzureAccount.id
                    }
                    else {
                        ""
                    }

                    ResourceGroup = $ResourceGroupName
                }

                Foundry = [PSCustomObject]@{
                    Project    = $FoundryProjectName
                    AIResource = $AiResourceName
                }

                ExistingDeployments = @(
                    $script:ExistingDeployments |
                        ForEach-Object {
                            [PSCustomObject]@{
                                Name = $_.name
                                State = $_.properties.provisioningState
                                Model = $_.properties.model.name
                                Version = $_.properties.model.version
                                SKU = $_.sku.name
                                Capacity = $_.sku.capacity
                            }
                        }
                )
            }

            $failureState |
                ConvertTo-Json -Depth 20 |
                Set-Content `
                    -LiteralPath $script:StateFile `
                    -Encoding UTF8
        }
    }
    catch {

        Write-Log `
            -Message "No fue posible actualizar el estado posterior al fallo." `
            -Level "ERROR"
    }

    try {

        Show-FinalSummary
    }
    catch {

        Write-Log `
            -Message "No fue posible generar el resumen final." `
            -Level "ERROR"
    }

    exit 1
}
finally {

    if ($script:TranscriptStarted) {

        try {

            Stop-Transcript |
                Out-Null
        }
        catch {

            # Nunca sobrescribir el error principal por un fallo del transcript.
        }
    }
}