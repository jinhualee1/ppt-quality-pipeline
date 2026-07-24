param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [ValidateRange(360, 4320)]
    [int]$Height = 1080
)

$ErrorActionPreference = "Stop"
$application = $null
$presentation = $null

function Release-ComObject {
    param([object]$Value)
    if ($null -ne $Value -and [System.Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

try {
    $resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDir)
    [System.IO.Directory]::CreateDirectory($resolvedOutput) | Out-Null

    Get-ChildItem -LiteralPath $resolvedOutput -Filter "page_*.png" -File -ErrorAction SilentlyContinue |
        Remove-Item -Force

    $application = New-Object -ComObject PowerPoint.Application
    $application.DisplayAlerts = 1
    try {
        $application.AutomationSecurity = 3
    } catch {
        # Older PowerPoint versions may not expose AutomationSecurity.
    }

    $presentation = $application.Presentations.Open($resolvedInput, $true, $true, $false)
    $slideWidth = [double]$presentation.PageSetup.SlideWidth
    $slideHeight = [double]$presentation.PageSetup.SlideHeight
    if ($slideWidth -le 0 -or $slideHeight -le 0) {
        throw "PowerPoint reported invalid slide dimensions."
    }

    $width = [Math]::Max(1, [int][Math]::Round($Height * ($slideWidth / $slideHeight)))
    $pages = New-Object System.Collections.Generic.List[string]

    for ($index = 1; $index -le $presentation.Slides.Count; $index += 1) {
        $slide = $null
        try {
            $slide = $presentation.Slides.Item($index)
            $name = "page_{0:D3}.png" -f $index
            $destination = Join-Path $resolvedOutput $name
            $slide.Export($destination, "PNG", $width, $Height)
            if (-not (Test-Path -LiteralPath $destination)) {
                throw "PowerPoint did not create $name."
            }
            $pages.Add($name)
        } finally {
            Release-ComObject $slide
        }
    }

    $manifest = [PSCustomObject]@{
        renderer = "microsoft-powerpoint"
        fidelity = "high"
        source = $resolvedInput
        width = $width
        height = $Height
        pages = $pages
    }
    $manifest |
        ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath (Join-Path $resolvedOutput "render_manifest.json") -Encoding UTF8
    $manifest | ConvertTo-Json -Depth 4 -Compress
} catch {
    Write-Error $_
    exit 1
} finally {
    if ($null -ne $presentation) {
        try {
            $presentation.Close()
        } catch {
        }
        Release-ComObject $presentation
    }
    if ($null -ne $application) {
        try {
            $application.Quit()
        } catch {
        }
        Release-ComObject $application
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
