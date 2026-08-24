param(
    [string]$BaseUrl = "http://localhost:5173",
    [int]$TimeoutSeconds = 15
)

$ErrorActionPreference = "Stop"

function Invoke-LennyRequest {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [ValidateSet("GET", "POST")] [string]$Method = "GET",
        [hashtable]$Body
    )

    $request = @{
        Uri = "$($BaseUrl.TrimEnd('/'))$Path"
        Method = $Method
        TimeoutSec = $TimeoutSeconds
        Headers = @{ "X-Request-ID" = "smoke-$([guid]::NewGuid())" }
    }
    if ($Body) {
        $request.ContentType = "application/json"
        $request.Body = $Body | ConvertTo-Json -Depth 5
    }
    Invoke-RestMethod @request
}

Write-Host "[1/5] Checking API liveness..."
$live = Invoke-LennyRequest -Path "/health/live"
if ($live.status -ne "ok") { throw "Liveness check returned '$($live.status)'" }

Write-Host "[2/5] Checking database readiness..."
$ready = Invoke-LennyRequest -Path "/health/ready"
if ($ready.status -ne "ok") { throw "Readiness check returned '$($ready.status)'" }

Write-Host "[3/5] Checking provider configuration..."
$config = Invoke-LennyRequest -Path "/api/v1/config"
if (-not $config.provider -or -not $config.model) { throw "Provider configuration is incomplete" }

Write-Host "[4/5] Creating a persisted smoke-test session..."
$session = Invoke-LennyRequest -Path "/api/v1/sessions" -Method POST -Body @{
    user_id = "smoke-evaluator"
    title = "Runtime smoke test"
}
if (-not $session.id) { throw "Session creation did not return an ID" }

Write-Host "[5/5] Exercising deterministic conversation routing..."
$turn = Invoke-LennyRequest -Path "/api/v1/sessions/$($session.id)/messages" -Method POST -Body @{
    content = "Hi"
}
if ($turn.assistant_message.status -ne "completed") {
    throw "Greeting turn did not complete"
}
if ($turn.grounded) { throw "Greeting should not invoke transcript retrieval" }

Write-Host ""
Write-Host "Smoke test passed." -ForegroundColor Green
Write-Host "Provider: $($config.provider) / $($config.model)"
Write-Host "Session:  $($session.id)"
