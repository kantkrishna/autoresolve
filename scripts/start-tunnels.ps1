# start-tunnels.ps1

Write-Host "[*] Starting AutoResolve Network Tunnels..." -ForegroundColor Cyan

# 1. Clean up any zombie kubectl processes hanging onto ports
Stop-Process -Name "kubectl" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 2. Spawn the tunnels in the background (Hidden windows)
Write-Host "[+] Forwarding API Gateway (8000:8000)..." -ForegroundColor Yellow
Start-Process -FilePath "kubectl" -ArgumentList "port-forward svc/autoresolve-api-gateway 8000:8000 -n autoresolve-ai" -WindowStyle Hidden

Write-Host "[+] Forwarding PostgreSQL (5433:5432)..." -ForegroundColor Yellow
Start-Process -FilePath "kubectl" -ArgumentList "port-forward svc/postgres 5433:5432 -n autoresolve-ai" -WindowStyle Hidden

Write-Host "[+] Forwarding Prometheus (9091:80)..." -ForegroundColor Yellow
Start-Process -FilePath "kubectl" -ArgumentList "port-forward svc/obs-stack-prometheus-server 9091:80 -n boutique-demo" -WindowStyle Hidden

Start-Sleep -Seconds 2
Write-Host "[SUCCESS] All tunnels established successfully!" -ForegroundColor Green
Write-Host "[INFO] You can now safely run your SRE Console." -ForegroundColor DarkCyan