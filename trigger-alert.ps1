# trigger-alert.ps1
# AutoResolve Enterprise Alert Simulation Ingestion Script

# 1. Force the active Windows console code page to UTF-8 at the OS level
chcp 65001 > $null
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 2. Generate emojis safely via UTF-32 codepoints (Bypasses file parsing bugs)
$Rocket = [char]::ConvertFromUtf32(0x1F680) # 🚀
$Party  = [char]::ConvertFromUtf32(0x1F389) # 🎉

$Uri = "http://localhost:8000/webhook/prometheus"
$SecretKey = "dev-secret-key" # Shared webhook token designed in Phase 5 security guardrails

# Define the Mock Alertmanager Payload matching the Pydantic data contract
$BodyObject = @{
    status      = "firing"
    alertname   = "HighMemoryUsage"
    service     = "payment-gateway"
    description = "Pod payment-gateway-pod-xyz memory usage is at 99%. OOMKilled imminent."
}

# Convert PowerShell object to a compressed JSON string
$JsonBody = $BodyObject | ConvertTo-Json -Compress

# Compute the HMAC SHA256 Cryptographic Signature to pass Phase 5 edge security
$HmacProcessor = New-Object System.Security.Cryptography.HMACSHA256
$HmacProcessor.Key = [System.Text.Encoding]::UTF8.GetBytes($SecretKey)
$BodyBytes = [System.Text.Encoding]::UTF8.GetBytes($JsonBody)
$HashBytes = $HmacProcessor.ComputeHash($BodyBytes)

# Convert hash bytes to a clean lowercase hex string string
$Signature = [System.BitConverter]::ToString($HashBytes).Replace("-", "").ToLower()

# Construct authenticated headers with tracking parameters
$Headers = @{
    "Content-Type"      = "application/json"
    "X-API-Key"         = $SecretKey
    "X-Signature"       = "sha256=$Signature"
}

Write-Host "$Rocket Dispatching secure alert payload to containerized FastAPI Ingestion Gateway..." -ForegroundColor Cyan
Write-Host "Target Endpoint: $Uri" -ForegroundColor Gray
Write-Host "Calculated Signature: sha256=$Signature`n" -ForegroundColor DarkGray

try {
    # Fire the authenticated network request directly into the Docker Compose subnet port
    $Response = Invoke-RestMethod -Uri $Uri -Method Post -Headers $Headers -Body $JsonBody
    
    Write-Host "$Party ALERT INGESTED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "HTTP Status: 202 Accepted" -ForegroundColor Green
    Write-Host "Tracking/Idempotency key: $($Response.tracking_id)" -ForegroundColor Yellow
}
catch {
    Write-Host "❌ ALERT TRANSMISSION FAILED!" -ForegroundColor Red
    Write-Error $_
}