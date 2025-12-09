# Test script for cache refresh behavior
# Usage: Run after starting the FastAPI server locally (uvicorn main:app --reload)

$base = "http://127.0.0.1:8000"

function Set-CacheMaxDate($dateString) {
    $body = @{ max_date = $dateString } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/_internal/test/set-cache-max-date" -Method Post -Body $body -ContentType "application/json"
}

function Call-Predict($location) {
    $body = @{ latitude = 13.27; longitude = 77.45; location = $location } | ConvertTo-Json
    Invoke-RestMethod -Uri "$base/predict/next-month" -Method Post -Body $body -ContentType "application/json"
}

Write-Host "--- Test 1: set cache max date to 2025-11-27 (stale) ---"
Set-CacheMaxDate "2025-11-27"
$response1 = Call-Predict "Kasaba, Nelamangala"
if ($response1 -and $response1.data -and $response1.data.predictions) {
    Write-Host "First prediction date (should be based on cached max+1):" $response1.data.predictions[0].date
} else {
    Write-Host "Failed to get prediction (first call)" 
}

Write-Host "\n--- Test 2: set cache max date to today ---"
$today = (Get-Date).ToString('yyyy-MM-dd')
Set-CacheMaxDate $today
$response2 = Call-Predict "Kasaba, Nelamangala"
if ($response2 -and $response2.data -and $response2.data.predictions) {
    Write-Host "Second prediction date (should be based on today+1):" $response2.data.predictions[0].date
} else {
    Write-Host "Failed to get prediction (second call)" 
}

Write-Host "\nCheck whether the two prediction start dates differ as expected." 
