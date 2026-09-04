# Hook Stop - don file log rong va nhac cap nhat tai lieu truoc khi ket thuc phien.

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$sessionsDir = Join-Path $projectRoot 'docs\sessions'

if (-not (Test-Path $sessionsDir)) { exit 0 }

$today = Get-Date -Format 'yyyy-MM-dd'
$log = Get-ChildItem -Path $sessionsDir -Filter "$today-*.md" -File -ErrorAction SilentlyContinue |
       Sort-Object Name | Select-Object -Last 1

if ($null -eq $log) { exit 0 }

# Template goc co 5 cho danh dau '_(chua ghi)_'. Con nguyen ca 5 nghia la agent
# chua ghi gi -> xoa de khong sinh rac trong repo.
$content = Get-Content -Path $log.FullName -Raw -Encoding UTF8
$placeholders = ([regex]::Matches($content, '_\(chua ghi\)_')).Count

if ($placeholders -ge 5) {
    Remove-Item -Path $log.FullName -Force
    exit 0
}

if ($placeholders -gt 0) {
    Write-Output "[NHAC] docs/sessions/$($log.Name) con $placeholders muc chua dien. Muc 'Ket qua test' phai co ket qua chay that."
}

Write-Output "[NHAC] Truoc khi ket thuc phien: docs/codebase-map.md da cap nhat chua? Checklist trong docs/plans/ da tick chua?"
