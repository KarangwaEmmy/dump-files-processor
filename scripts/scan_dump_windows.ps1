Param(
    [string]$Path = 'C:\Dump',
    [string]$Codes = '51381,51380,51387,51386,RAA520P',
    [string]$Out = 'dump_report.json'
)

$codes = $Codes -split ',' | ForEach-Object { $_.Trim() }
$report = @{}

if (-not (Test-Path $Path)) {
    Write-Error "Path $Path not found"
    exit 1
}

Get-ChildItem -Path $Path -File | ForEach-Object {
    $file = $_.FullName
    $sha256 = (Get-FileHash -Algorithm SHA256 -Path $file).Hash
    $sha1 = (Get-FileHash -Algorithm SHA1 -Path $file).Hash
    $text = Get-Content -Raw -ErrorAction SilentlyContinue -Path $file
    $found = @()
    foreach ($c in $codes) {
        if ($null -ne ($text -match "\b$c\b")) { $found += $c }
    }
    $ts_like = @()
    if ($text) {
        $ts_like = [regex]::Matches($text, '20\d{6}\s*\d{6,9}|20\d{10,12}') | ForEach-Object { $_.Value }
    }
    $report[$file] = @{
        sha256 = $sha256
        sha1 = $sha1
        size = $_.Length
        mtime = $_.LastWriteTimeUtc
        ctime = $_.CreationTimeUtc
        found_codes = $found
        ts_like = $ts_like
    }
}

$report | ConvertTo-Json -Depth 5 | Out-File -FilePath $Out -Encoding UTF8
Write-Output "Saved report to $Out"
