# Render a static WPF layout preview from the dashboard definition, without opening a window.
# This is a layout preview, not a capture of a running SimHub overlay.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase
$name = 'guysmiley222 - Basic Lap Timer'
$dir = Join-Path $PSScriptRoot "dashboard\$name"
$dashboard = Get-Content -LiteralPath (Join-Path $dir "$name.djson") -Raw | ConvertFrom-Json
$samples = @{'Connection status'='CURRENT LAP'; 'Current lap'='1:18.395'; 'Last lap'='1:20.123'; 'Best lap'='1:18.012'}
$canvas = New-Object System.Windows.Controls.Canvas
$canvas.Width = $dashboard.BaseWidth
$canvas.Height = $dashboard.BaseHeight
$brush = New-Object System.Windows.Media.BrushConverter
foreach ($item in $dashboard.Screens[0].Items) {
    if ($item.IsRectangleItem) {
        $control = New-Object System.Windows.Shapes.Rectangle
        $control.Fill = $brush.ConvertFromString($item.BackgroundColor)
        $control.RadiusX = $item.BorderStyle.RadiusTopLeft
        $control.RadiusY = $item.BorderStyle.RadiusTopLeft
    } else {
        $control = New-Object System.Windows.Controls.Border
        $label = New-Object System.Windows.Controls.TextBlock
        $label.Text = $item.Text
        if ($samples.ContainsKey($item.Name)) { $label.Text = $samples[$item.Name] }
        $label.FontFamily = New-Object System.Windows.Media.FontFamily($item.Font)
        $label.FontSize = $item.FontSize
        $label.Foreground = $brush.ConvertFromString($item.TextColor)
        $label.VerticalAlignment = 'Center'
        $control.Child = $label
    }
    $control.Width = $item.Width
    $control.Height = $item.Height
    [System.Windows.Controls.Canvas]::SetLeft($control, $item.Left)
    [System.Windows.Controls.Canvas]::SetTop($control, $item.Top)
    $null = $canvas.Children.Add($control)
}
$size = New-Object System.Windows.Size(320,150)
$canvas.Measure($size)
$canvas.Arrange((New-Object System.Windows.Rect($size)))
$canvas.UpdateLayout()
$bitmap = New-Object System.Windows.Media.Imaging.RenderTargetBitmap(320,150,96,96,[System.Windows.Media.PixelFormats]::Pbgra32)
$bitmap.Render($canvas)
$encoder = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
$encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
$stream = [IO.File]::Create((Join-Path $PSScriptRoot 'preview.png'))
try { $encoder.Save($stream) } finally { $stream.Dispose() }
foreach ($suffix in @('.djson.png', '.djson.00.png')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'preview.png') -Destination (Join-Path $dir "$name$suffix")
}
Write-Output 'Created static WPF layout preview and package thumbnails'
