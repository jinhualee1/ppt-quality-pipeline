$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$testRoot = Join-Path $projectRoot "tmp\powerpoint-renderer-test\$stamp"
$pptx = Join-Path $testRoot "synthetic-render-test.pptx"
$pages = Join-Path $testRoot "pages"

[System.IO.Directory]::CreateDirectory($testRoot) | Out-Null

& (Join-Path $PSScriptRoot "create_test_pptx.ps1") -OutputPath $pptx | Out-Null
if (-not (Test-Path -LiteralPath $pptx)) {
    throw "Could not create the synthetic PowerPoint fixture."
}

& (Join-Path $PSScriptRoot "render_pptx_powerpoint.ps1") `
    -InputPath $pptx `
    -OutputDir $pages `
    -Height 1080 | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $pages "render_manifest.json"))) {
    throw "PowerPoint rendering failed."
}

Add-Type -AssemblyName System.Drawing
$results = foreach ($page in Get-ChildItem -LiteralPath $pages -Filter "page_*.png" -File) {
    $image = [System.Drawing.Image]::FromFile($page.FullName)
    try {
        [PSCustomObject]@{
            page = $page.Name
            width = $image.Width
            height = $image.Height
            bytes = $page.Length
        }
    } finally {
        $image.Dispose()
    }
}

if (@($results).Count -ne 3) {
    throw "Expected 3 rendered pages, found $(@($results).Count)."
}
if (@($results | Where-Object { $_.width -ne 1920 -or $_.height -ne 1080 }).Count -gt 0) {
    throw "One or more rendered pages have unexpected dimensions."
}

[PSCustomObject]@{
    ok = $true
    renderer = "microsoft-powerpoint"
    fidelity = "high"
    output = $testRoot
    pages = $results
} | ConvertTo-Json -Depth 5
