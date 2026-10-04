param([string]$SimHubPath = 'C:\Program Files (x86)\SimHub')
$ErrorActionPreference = 'Stop'
$null = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'Newtonsoft.Json.dll'))
$assembly = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'SimHub.Plugins.dll'))
$null = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$catalog = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'themes.json') -Raw | ConvertFrom-Json
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
    if ($parameterName -ne 'Settings.Theme.Key') { throw "Unexpected theme parameter: $parameterName" }
    $evaluationArgs.Result = $script:themeKey
}
$repoRoot = Split-Path $PSScriptRoot
$checks = 0
foreach ($entry in @(
    @{Folder='Basic Lap Timer'; Name='guysmiley222 - Basic Lap Timer'},
    @{Folder='Overlay Template'; Name='guysmiley222 - Overlay Template'},
    @{Folder='Advanced Lap Timer'; Name='guysmiley222 - Advanced Lap Timer'}
)) {
    $dir = Join-Path $repoRoot ($entry.Folder + '\dashboard\' + $entry.Name)
    $json = Get-Content -LiteralPath (Join-Path $dir ($entry.Name + '.djson')) -Raw
    $document = $json | ConvertFrom-Json
    $settings = New-Object Newtonsoft.Json.JsonSerializerSettings
    $settings.TypeNameHandling = [Newtonsoft.Json.TypeNameHandling]::Auto
    $previousDirectory = [Environment]::CurrentDirectory
    try {
        [Environment]::CurrentDirectory = $SimHubPath
        $model = [Newtonsoft.Json.JsonConvert]::DeserializeObject(
            $json, $assembly.GetType('SimHub.Plugins.OutputPlugins.GraphicalDash.Dashboard'), $settings)
        $metadataJson = Get-Content -LiteralPath (Join-Path $dir ($entry.Name + '.djson.metadata')) -Raw
        $metadata = [Newtonsoft.Json.JsonConvert]::DeserializeObject(
            $metadataJson, $assembly.GetType('SimHub.Plugins.OutputPlugins.GraphicalDash.DashboardMetadata'), $settings)
    } finally { [Environment]::CurrentDirectory = $previousDirectory }
    $dropdown = $model.SettingsBuilder.Settings[0]
    $metadataDropdown = $metadata.SettingsBuilder.Settings[0]
    if ($null -eq $metadataDropdown -or $metadataDropdown.PropertyName -ne 'Theme' -or
        $metadataDropdown.Options.Count -ne 6 -or $metadataDropdown.Id -ne $dropdown.Id) {
        throw "Theme dropdown missing from dashboard metadata: $($entry.Name)"
    }
    if ($dropdown.GetType().Name -ne 'ComboboxEntry' -or $dropdown.DefaultValue -ne 'current' -or
        $dropdown.PropertyName -ne 'Theme' -or $dropdown.Options.Count -ne 6) {
        throw "Theme dropdown failed to load: $($entry.Name)"
    }
    $expectedKeys = @($catalog.themes | ForEach-Object key) -join ','
    if ((@($dropdown.Options | ForEach-Object Key) -join ',') -ne $expectedKeys) { throw 'Dropdown option mismatch' }
    foreach ($key in @($catalog.themes | ForEach-Object key) + @($null,'unknown','')) {
        $script:themeKey = $key
        $selected = @($catalog.themes | Where-Object {$_.key -eq $key})
        if ($selected.Count -eq 0) { $selected = @($catalog.themes[0]) }
        foreach ($item in $document.Screens[0].Items) {
            $target = if ($item.IsRectangleItem) { 'BackgroundColor' } else { 'TextColor' }
            $role = if ($item.IsRectangleItem) { 'panel' }
                elseif ($item.Name -in @('Connection status','Title')) { 'heading' }
                elseif ($item.Name -in @('Last label','Best label','Label') -or $item.Name -like '* label') { 'muted' }
                elseif ($item.Name -in @('Accent','Success','Warning','Danger')) { $item.Name.ToLowerInvariant() }
                else { 'primary' }
            $expression = New-Object NCalc.Expression($item.Bindings.$target.Formula.Expression)
            $expression.add_EvaluateFunction($functions)
            $expression.add_EvaluateParameter($parameters)
            $actual = $expression.Evaluate()
            $alpha = if ($role -eq 'panel') { 'D9' } else { 'FF' }
            $expected = '#' + $alpha + $selected[0].colors.$role.Substring(1)
            if ($actual -ne $expected) { throw "Theme mismatch: $key / $($item.Name): $actual != $expected" }
            $checks++
        }
    }
    Write-Output "PASS: installed SimHub models and six themes plus null/unknown/empty selection: $($entry.Name)"
}
Write-Output "PASS: $checks color-binding checks. Runtime UI selection and persistence still require a SimHub session."
