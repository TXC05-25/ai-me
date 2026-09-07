$cfg = Join-Path $env:USERPROFILE '.ssh\config'
if (Test-Path $cfg) {
    Write-Host "=== existing $cfg ==="
    Get-Content $cfg
    Write-Host "=== end ==="
} else {
    Write-Host "$cfg not found"
}
