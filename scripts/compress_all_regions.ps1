$7z = "F:\soft\7-Zip\7z.exe"
$models = "D:\God of War Ragnarok_extracted\models"
$archives = "D:\God of War Ragnarok_extracted\archives"
$logFile = "$archives\compress_log.txt"

# Regions sorted by size (ascending), skip cutscenes (already done)
$regions = @(
    @{name="helheim";      split=$false},
    @{name="characters";   split=$false},
    @{name="muspelheim";   split=$false},
    @{name="asgard";       split=$false},
    @{name="base";         split=$false},
    @{name="valhalla";     split=$false},
    @{name="jotunheim";    split=$false},
    @{name="alfheim";      split=$false},
    @{name="niflheim";     split=$false},
    @{name="svartalfheim"; split=$true},
    @{name="vanaheim";     split=$true},
    @{name="midgard";      split=$true}
)

foreach ($r in $regions) {
    $name = $r.name
    $src = "$models\$name"
    $dst = "$archives\$name.7z"
    
    # Skip if already done (check for .7z or .7z.001)
    $exists = Test-Path $dst
    if (-not $exists) { $exists = Test-Path "$dst.001" }
    if ($exists) {
        $msg = "[SKIP] $name already archived"
        Write-Host $msg
        Add-Content $logFile "$(Get-Date -Format 'HH:mm:ss') $msg"
        continue
    }
    
    $startTime = Get-Date
    $msg = "[START] $name at $(Get-Date -Format 'HH:mm:ss')"
    Write-Host $msg
    Add-Content $logFile "$(Get-Date -Format 'HH:mm:ss') $msg"
    
    if ($r.split) {
        & $7z a -t7z -mx=5 -mmt=8 -v10g $dst "$src\*" 2>&1 | Out-Null
    } else {
        & $7z a -t7z -mx=5 -mmt=8 $dst "$src\*" 2>&1 | Out-Null
    }
    
    $elapsed = ((Get-Date) - $startTime).TotalMinutes
    $totalSize = 0
    Get-ChildItem "$archives\$name.7z*" -ErrorAction SilentlyContinue | ForEach-Object { $totalSize += $_.Length }
    
    $msg = "[DONE]  $name in {0:N1} min, archive={1:N2} GB" -f $elapsed, ($totalSize/1GB)
    Write-Host $msg
    Add-Content $logFile "$(Get-Date -Format 'HH:mm:ss') $msg"
}

$msg = "[ALL DONE] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "`n$msg"
Add-Content $logFile $msg

# Summary
Write-Host "`n=== Final Archive Summary ==="
Add-Content $logFile "=== Final Archive Summary ==="
$grandTotal = 0
Get-ChildItem $archives -Filter "*.7z*" -File | Sort-Object Name | ForEach-Object {
    $gb = $_.Length / 1GB
    $grandTotal += $gb
    $line = "{0,-35} {1,8:N2} GB" -f $_.Name, $gb
    Write-Host $line
    Add-Content $logFile $line
}
$line = "TOTAL: {0:N2} GB" -f $grandTotal
Write-Host $line
Add-Content $logFile $line