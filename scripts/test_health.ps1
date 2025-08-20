<#
.SYNOPSIS
    Tests the health check endpoint of the SmartLinks API.
.DESCRIPTION
    This script sends a GET request to the /api/health endpoint and displays the response.
    It's useful for verifying that the API is running and responding correctly.
.EXAMPLE
    .\test_health.ps1
#>

$ErrorActionPreference = "Stop"
$apiUrl = "http://localhost:8000/api/health"

try {
    Write-Host "Testing API health check at $apiUrl" -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get -ContentType "application/json"
    
    # Format the JSON output with indentation
    $formattedJson = $response | ConvertTo-Json -Depth 10 -Compress:$false
    
    Write-Host "`n[SUCCESS] API is healthy!" -ForegroundColor Green
    Write-Host $formattedJson -ForegroundColor Green
    exit 0
}
catch [System.Net.WebException] {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $statusDescription = $_.Exception.Response.StatusDescription
    $errorDetails = $_.ErrorDetails.Message
    
    Write-Host "`n[ERROR] API request failed" -ForegroundColor Red
    Write-Host "Status Code: $statusCode ($statusDescription)" -ForegroundColor Red
    
    if ($errorDetails) {
        try {
            $errorJson = $errorDetails | ConvertFrom-Json
            $formattedError = $errorJson | ConvertTo-Json -Depth 5 -Compress:$false
            Write-Host $formattedError -ForegroundColor Red
        }
        catch {
            Write-Host "Response: $errorDetails" -ForegroundColor Red
        }
    }
    
    exit 1
}
catch {
    Write-Host "`n[ERROR] An unexpected error occurred: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray
    exit 1
}
