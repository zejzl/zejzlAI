# Test Budget Alert System
# Run this after configuring DISCORD_WEBHOOK_URL in .env

Write-Host "Testing Budget Alert System..." -ForegroundColor Cyan
Write-Host ""

# Test 1: WARNING (85% usage)
Write-Host "Test 1: WARNING alert (85% usage)" -ForegroundColor Yellow
$body1 = @{
    task_id = "test_warning"
    tokens_used = 8500
    budget_limit = 10000
} | ConvertTo-Json

$result1 = curl.exe -s -X POST "http://localhost:8000/api/swarm/test-alert" `
    -H "Content-Type: application/json" `
    -d $body1 | ConvertFrom-Json

Write-Host "  Result: $($result1.message)" -ForegroundColor Green
Write-Host "  Alert sent: $($result1.result.alert_sent)"
Write-Host ""

Start-Sleep -Seconds 2

# Test 2: CRITICAL (92% usage)
Write-Host "Test 2: CRITICAL alert (92% usage)" -ForegroundColor Red
$body2 = @{
    task_id = "test_critical"
    tokens_used = 9200
    budget_limit = 10000
} | ConvertTo-Json

$result2 = curl.exe -s -X POST "http://localhost:8000/api/swarm/test-alert" `
    -H "Content-Type: application/json" `
    -d $body2 | ConvertFrom-Json

Write-Host "  Result: $($result2.message)" -ForegroundColor Green
Write-Host "  Alert sent: $($result2.result.alert_sent)"
Write-Host ""

Start-Sleep -Seconds 2

# Test 3: EXHAUSTED (105% usage)
Write-Host "Test 3: EXHAUSTED alert (105% usage)" -ForegroundColor Magenta
$body3 = @{
    task_id = "test_exhausted"
    tokens_used = 10500
    budget_limit = 10000
} | ConvertTo-Json

$result3 = curl.exe -s -X POST "http://localhost:8000/api/swarm/test-alert" `
    -H "Content-Type: application/json" `
    -d $body3 | ConvertFrom-Json

Write-Host "  Result: $($result3.message)" -ForegroundColor Green
Write-Host "  Alert sent: $($result3.result.alert_sent)"
Write-Host ""

Write-Host "Done! Check your Discord channel for 3 alerts." -ForegroundColor Cyan
Write-Host "Dashboard: http://localhost:8000/blackboard" -ForegroundColor Blue
