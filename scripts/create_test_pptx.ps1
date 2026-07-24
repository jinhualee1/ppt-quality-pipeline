param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$application = $null
$presentation = $null

function Rgb {
    param([int]$Red, [int]$Green, [int]$Blue)
    return $Red + ($Green * 256) + ($Blue * 65536)
}

function Utf8 {
    param([string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Value))
}

function Release-ComObject {
    param([object]$Value)
    if ($null -ne $Value -and [System.Runtime.InteropServices.Marshal]::IsComObject($Value)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Value)
    }
}

function Add-Text {
    param(
        [object]$Slide,
        [string]$Text,
        [float]$Left,
        [float]$Top,
        [float]$Width,
        [float]$Height,
        [float]$Size,
        [int]$Color,
        [bool]$Bold = $false
    )
    $shape = $Slide.Shapes.AddTextbox(1, $Left, $Top, $Width, $Height)
    $shape.TextFrame.TextRange.Text = $Text
    $shape.TextFrame.TextRange.Font.Name = "Microsoft YaHei"
    $shape.TextFrame.TextRange.Font.Size = $Size
    $shape.TextFrame.TextRange.Font.Bold = if ($Bold) { -1 } else { 0 }
    $shape.TextFrame.TextRange.Font.Color.RGB = $Color
    $shape.TextFrame.MarginLeft = 0
    $shape.TextFrame.MarginRight = 0
    $shape.TextFrame.MarginTop = 0
    $shape.TextFrame.MarginBottom = 0
    return $shape
}

try {
    $target = [System.IO.Path]::GetFullPath($OutputPath)
    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($target)) | Out-Null
    $application = New-Object -ComObject PowerPoint.Application
    $application.DisplayAlerts = 1
    $presentation = $application.Presentations.Add()
    $presentation.PageSetup.SlideWidth = 960
    $presentation.PageSetup.SlideHeight = 540

    $navy = Rgb 23 33 43
    $teal = Rgb 10 147 139
    $coral = Rgb 238 118 93
    $amber = Rgb 233 180 76
    $paper = Rgb 248 250 251
    $muted = Rgb 94 107 117

    for ($number = 1; $number -le 3; $number += 1) {
        $slide = $presentation.Slides.Add($number, 12)
        $background = $slide.Shapes.AddShape(1, 0, 0, 960, 540)
        $background.Fill.ForeColor.RGB = $paper
        $background.Line.Visible = 0
        $background.ZOrder(1)

        $accent = $slide.Shapes.AddShape(1, 0, 0, 18, 540)
        $accent.Fill.ForeColor.RGB = @($teal, $coral, $amber)[$number - 1]
        $accent.Line.Visible = 0

        if ($number -eq 1) {
            [void](Add-Text $slide (Utf8 "6auY5L+d55yfIFBQVFgg5riy5p+T") 64 86 640 70 34 $navy $true)
            [void](Add-Text $slide (Utf8 "5Y6f55SfIFBvd2VyUG9pbnQg5a+85Ye65L+d55WZ5a2X5L2T44CB5b2i54q244CB6YWN6Imy5LiO6aG16Z2i5Yeg5L2V5YWz57O744CC") 64 178 610 72 18 $muted)
            $panel = $slide.Shapes.AddShape(1, 700, 90, 190, 310)
            $panel.Fill.ForeColor.RGB = $navy
            $panel.Line.Visible = 0
            foreach ($offset in 0, 1, 2) {
                $bar = $slide.Shapes.AddShape(1, 735 + ($offset * 48), 330 - ($offset * 58), 28, 50 + ($offset * 58))
                $bar.Fill.ForeColor.RGB = @($amber, $coral, $teal)[$offset]
                $bar.Line.Visible = 0
            }
        } elseif ($number -eq 2) {
            [void](Add-Text $slide (Utf8 "5riy5p+T5ZCO56uv5LyY5YWI57qn") 64 60 540 55 30 $navy $true)
            [void](Add-Text $slide (Utf8 "57O757uf6Ieq5Yqo6YCJ5oup5Y+v55So55qE5pyA5L2z5ZCO56uv77yM5bm25Zyo5q+P5Lu95oql5ZGK5Lit6K6w5b2V5L+d55yf5bqm44CC") 64 126 720 54 17 $muted)
            $labels = @("Microsoft PowerPoint", "LibreOffice + PDF", (Utf8 "5paH5a2X6aKE6KeI5YWc5bqV"))
            for ($index = 0; $index -lt $labels.Count; $index += 1) {
                $box = $slide.Shapes.AddShape(1, 64 + ($index * 286), 235, 245, 145)
                $box.Fill.ForeColor.RGB = if ($index -eq 0) { $navy } else { Rgb 255 255 255 }
                $box.Line.ForeColor.RGB = @($navy, $teal, $amber)[$index]
                $box.Line.Weight = 2
                $textColor = if ($index -eq 0) { Rgb 255 255 255 } else { $navy }
                [void](Add-Text $slide $labels[$index] (84 + ($index * 286)) 270 205 70 18 $textColor $true)
            }
        } else {
            [void](Add-Text $slide (Utf8 "5Y+v5L+h44CB5Y+v6L+95rqv55qE5Lqk5LuY6K+B5o2u") 64 72 620 55 30 $navy $true)
            [void](Add-Text $slide (Utf8 "5q+P5LiA5byg5riy5p+T6aG16Z2i6YO96IO96L+95rqv5Yiw5rqQ5paH5Lu25LiO5a6e6ZmF5riy5p+T5ZCO56uv44CC") 64 140 690 50 18 $muted)
            $checks = @(
                (Utf8 "5Y6f55Sf6aG16Z2i5Yeg5L2V"),
                (Utf8 "6auY5YiG6L6o546HIFBORyDpobXpnaI="),
                (Utf8 "5ZCO56uv5LiO5L+d55yf5bqm5YWD5pWw5o2u")
            )
            for ($index = 0; $index -lt $checks.Count; $index += 1) {
                $dot = $slide.Shapes.AddShape(9, 72, 236 + ($index * 74), 26, 26)
                $dot.Fill.ForeColor.RGB = $teal
                $dot.Line.Visible = 0
                [void](Add-Text $slide $checks[$index] 118 (232 + ($index * 74)) 650 42 20 $navy $false)
            }
        }
        [void](Add-Text $slide ("0{0}" -f $number) 864 492 42 22 11 $muted)
        Release-ComObject $slide
    }

    $presentation.SaveAs($target, 24)
    Write-Output $target
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
