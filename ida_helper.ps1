function Call-Ida([string]$tool, $arguments) {
    $body = @{ jsonrpc="2.0"; id=1; method="tools/call"; params=@{ name=$tool; arguments=$arguments } } | ConvertTo-Json -Depth 10
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:13337/mcp" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
    $j = $r.Content | ConvertFrom-Json
    if ($j.result) { $j.result.content | ForEach-Object { $_.text } } elseif ($j.error) { $j.error } else { $j }
}
function Decompile-Ida([string]$addr) {
    Call-Ida "decompile" @{ addr=$addr }
}
function Get-Bytes-Ida([string]$addr, [int]$size) {
    Call-Ida "get_bytes" @{ addr=$addr; size=$size }
}
function Xrefs-To-Ida([string]$addr) {
    Call-Ida "xrefs_to" @{ addr=$addr }
}