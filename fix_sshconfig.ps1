# Update SSH config to add Port 2222 for 218.244.140.70
$cfg = Join-Path $env:USERPROFILE '.ssh\config'
$content = Get-Content $cfg -Raw

# Backup once
$bak = $cfg + '.bak.' + (Get-Date -Format 'yyyyMMddHHmmss')
Copy-Item $cfg $bak

# Make sure Port 2222 line exists within the 218.244.140.70 block
$pattern = '(?ms)(Host\s+218\.244\.140\.70[\s\S]*?)(?=^Host\s|\z)'
if ($content -notmatch "(?ms)Host\s+218\.244\.140\.70[\s\S]*?\n\s*Port\s+\d+") {
    $newContent = $content -replace $pattern, ("$1  Port 2222`n")
} else {
    # Has Port line - replace if it's not 2222
    $newContent = [regex]::Replace($content, "(?ms)(Host\s+218\.244\.140\.70[\s\S]*?\n\s*)Port\s+\d+", ('$1Port 2222'))
}

$newContent | Set-Content $cfg -NoNewline -Encoding UTF8

Write-Host "=== new config ==="
Get-Content $cfg
