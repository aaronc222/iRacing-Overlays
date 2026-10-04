# Static WPF rendering of the generated theme bindings. No desktop window is opened.
param(
    [Parameter(Mandatory=$true)][string]$OverlayRoot,
    [Parameter(Mandatory=$true)][string]$Name,
    [string]$SimHubPath = 'C:\Program Files (x86)\SimHub'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase
$null = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$dir = Join-Path $OverlayRoot "dashboard\$Name"
$dashboard = Get-Content -LiteralPath (Join-Path $dir "$Name.djson") -Raw | ConvertFrom-Json
$catalog = Get-Content -LiteralPath (Join-Path $dir 'themes.json') -Raw | ConvertFrom-Json
$samples = Get-Content -LiteralPath (Join-Path $dir 'preview-samples.json') -Raw | ConvertFrom-Json
$brushConverter = New-Object System.Windows.Media.BrushConverter
$script:themeKey = 'current'
$functions = [NCalc.EvaluateFunctionHandler] {
    param($functionName, $evaluationArgs)
    if ($functionName -eq 'isnull') {
        $value = $evaluationArgs.Parameters[0].Evaluate()
        $evaluationArgs.Result = if ($null -eq $value) { $evaluationArgs.Parameters[1].Evaluate() } else { $value }
    }
}
$parameters = [NCalc.EvaluateParameterHandler] {
    param($parameterName, $evaluationArgs)
    if ($parameterName -ne 'Settings.Theme.Key') { throw "Unexpected parameter: $parameterName" }
    $evaluationArgs.Result = $script:themeKey
}
function ThemeColor($item, [string]$property) {
    $expression = New-Object NCalc.Expression($item.Bindings.$property.Formula.Expression)
    $expression.add_EvaluateFunction($functions)
    $expression.add_EvaluateParameter($parameters)
    return $expression.Evaluate()
}
function New-Panel([string]$key) {
    $script:themeKey = $key
    $canvas = New-Object System.Windows.Controls.Canvas
    $canvas.Width = $dashboard.BaseWidth
    $canvas.Height = $dashboard.BaseHeight
    foreach ($item in $dashboard.Screens[0].Items) {
        if ($item.IsRectangleItem) {
            $control = New-Object System.Windows.Shapes.Rectangle
            $control.Fill = $brushConverter.ConvertFromString((ThemeColor $item 'BackgroundColor'))
            $control.RadiusX = $item.BorderStyle.RadiusTopLeft
            $control.RadiusY = $item.BorderStyle.RadiusTopLeft
        } else {
            $control = New-Object System.Windows.Controls.Border
            $label = New-Object System.Windows.Controls.TextBlock
            $label.Text = $item.Text
            if ($samples.PSObject.Properties[$item.Name]) { $label.Text = $samples.($item.Name) }
            $label.FontFamily = New-Object System.Windows.Media.FontFamily($item.Font)
            $label.FontSize = $item.FontSize
            $label.Foreground = $brushConverter.ConvertFromString((ThemeColor $item 'TextColor'))
            $label.VerticalAlignment = 'Center'
            $control.Child = $label
        }
        $control.Width = $item.Width
        $control.Height = $item.Height
        [System.Windows.Controls.Canvas]::SetLeft($control, $item.Left)
        [System.Windows.Controls.Canvas]::SetTop($control, $item.Top)
        $null = $canvas.Children.Add($control)
    }
    return $canvas
}
function Save-Canvas($canvas, [string]$path) {
    $size = New-Object System.Windows.Size($canvas.Width,$canvas.Height)
    $canvas.Measure($size)
    $canvas.Arrange((New-Object System.Windows.Rect($size)))
    $canvas.UpdateLayout()
    $bitmap = New-Object System.Windows.Media.Imaging.RenderTargetBitmap(
        [int]$canvas.Width,[int]$canvas.Height,96,96,[System.Windows.Media.PixelFormats]::Pbgra32)
    $bitmap.Render($canvas)
    $encoder = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
    $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
    $stream = [IO.File]::Create($path)
    try { $encoder.Save($stream) } finally { $stream.Dispose() }
}
$previewDir = Join-Path $OverlayRoot 'previews'
$null = New-Item -ItemType Directory -Path $previewDir -Force
$sheet = New-Object System.Windows.Controls.Canvas
$cellWidth = $dashboard.BaseWidth + 20
$cellHeight = $dashboard.BaseHeight + 42
$sheet.Width = $cellWidth * 2
$sheet.Height = $cellHeight * $catalog.themes.Count
$row = 0
foreach ($theme in $catalog.themes) {
    Save-Canvas (New-Panel $theme.key) (Join-Path $previewDir ($theme.key + '.png'))
    for ($column=0; $column -lt 2; $column++) {
        $cell = New-Object System.Windows.Controls.Canvas
        $cell.Width = $cellWidth
        $cell.Height = $cellHeight
        $cell.Background = $brushConverter.ConvertFromString(@('#141820','#F2F2F2')[$column])
        $caption = New-Object System.Windows.Controls.TextBlock
        $caption.Text = $theme.label + @(' / dark backdrop',' / light backdrop')[$column]
        $caption.FontFamily = New-Object System.Windows.Media.FontFamily('Consolas')
        $caption.FontSize = 13
        $caption.Foreground = $brushConverter.ConvertFromString(@('#FFFFFF','#202020')[$column])
        [System.Windows.Controls.Canvas]::SetLeft($caption,10)
        [System.Windows.Controls.Canvas]::SetTop($caption,8)
        $null = $cell.Children.Add($caption)
        $panel = New-Panel $theme.key
        [System.Windows.Controls.Canvas]::SetLeft($panel,10)
        [System.Windows.Controls.Canvas]::SetTop($panel,32)
        $null = $cell.Children.Add($panel)
        [System.Windows.Controls.Canvas]::SetLeft($cell,$column*$cellWidth)
        [System.Windows.Controls.Canvas]::SetTop($cell,$row*$cellHeight)
        $null = $sheet.Children.Add($cell)
    }
    $row++
}
Save-Canvas $sheet (Join-Path $OverlayRoot 'themes-preview.png')
Copy-Item -LiteralPath (Join-Path $previewDir 'current.png') -Destination (Join-Path $OverlayRoot 'preview.png')
foreach ($suffix in @('.djson.png','.djson.00.png')) {
    Copy-Item -LiteralPath (Join-Path $OverlayRoot 'preview.png') -Destination (Join-Path $dir "$Name$suffix")
}
Write-Output "PASS: rendered all six theme bindings on light and dark backgrounds: $OverlayRoot"
