# Run with Windows PowerShell 5.1: powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File .\verify.ps1
# Loads the locally installed SimHub model and NCalc assemblies; does not install the dashboard.
param([string]$SimHubPath = 'C:\Program Files (x86)\SimHub', [switch]$Live)
$ErrorActionPreference = 'Stop'
$name = 'guysmiley222 - Basic Lap Timer'
$source = Join-Path $PSScriptRoot "dashboard\$name\$name.djson"
$null = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'Newtonsoft.Json.dll'))
$assembly = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'SimHub.Plugins.dll'))
$null = [Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$json = [IO.File]::ReadAllText($source)
$settings = New-Object Newtonsoft.Json.JsonSerializerSettings
$settings.TypeNameHandling = [Newtonsoft.Json.TypeNameHandling]::Auto
$previousDirectory = [Environment]::CurrentDirectory
try {
    # SimHub's SettingsBuilder type resolver scans its installation directory.
    [Environment]::CurrentDirectory = $SimHubPath
    $model = [Newtonsoft.Json.JsonConvert]::DeserializeObject(
        $json, $assembly.GetType('SimHub.Plugins.OutputPlugins.GraphicalDash.Dashboard'), $settings)
} finally { [Environment]::CurrentDirectory = $previousDirectory }
if ($model.BaseWidth -ne 320 -or $model.BaseHeight -ne 150 -or $model.Screens.Count -ne 1) {
    throw 'Unexpected dashboard dimensions or screen count'
}
if (@($model.GetAllChildItems()).Count -ne 8) { throw 'Dashboard component count mismatch' }
Write-Output 'PASS: deserialized all components using installed SimHub dashboard models'

$document = $json | ConvertFrom-Json
$script:values = @{}
$functionHandler = [NCalc.EvaluateFunctionHandler] {
    param($functionName, $functionArgs)
    switch ($functionName.ToLowerInvariant()) {
        'isnull' {
            $v = $functionArgs.Parameters[0].Evaluate()
            if ($null -eq $v) { $functionArgs.Result = $functionArgs.Parameters[1].Evaluate() }
            else { $functionArgs.Result = $v }
        }
        'format' {
            $v = $functionArgs.Parameters[0].Evaluate()
            $fmt = $functionArgs.Parameters[1].Evaluate()
            if ($null -eq $v) { $functionArgs.Result = $null }
            else { $functionArgs.Result = $v.ToString($fmt) }
        }
        'replace' {
            $functionArgs.Result = ([string]$functionArgs.Parameters[0].Evaluate()).Replace(
                [string]$functionArgs.Parameters[1].Evaluate(),
                [string]$functionArgs.Parameters[2].Evaluate())
        }
    }
}
$parameterHandler = [NCalc.EvaluateParameterHandler] {
    param($parameterName, $parameterArgs)
    $parameterArgs.Result = $script:values[$parameterName]
}
function Evaluate-Formula([string]$formula) {
    $expression = New-Object NCalc.Expression($formula)
    $expression.add_EvaluateFunction($functionHandler)
    $expression.add_EvaluateParameter($parameterHandler)
    return $expression.Evaluate()
}
function Assert-Equal($actual, $expected, $label) {
    if ($actual -ne $expected) { throw "$label expected '$expected', got '$actual'" }
}
$script:values['DataCorePlugin.GameRunning'] = $true
$script:values['DataCorePlugin.CurrentGame'] = 'IRacing'
$properties = @('CurrentLapTime', 'LastLapTime', 'BestLapTime')
$timers = @($document.Screens[0].Items | Where-Object { $_.Name -in @('Current lap','Last lap','Best lap') })
foreach ($timer in $timers) {
    foreach ($case in @(
        @{Ms=78395; Expected='1:18.395'},
        @{Ms=59999; Expected='0:59.999'},
        @{Ms=60000; Expected='1:00.000'},
        @{Ms=612345; Expected='10:12.345'},
        @{Ms=0; Expected='--:--.---'},
        @{Ms=$null; Expected='--:--.---'}
    )) {
        foreach ($property in $properties) {
            $v = $null
            if ($null -ne $case.Ms) { $v = [TimeSpan]::FromMilliseconds($case.Ms) }
            $script:values["DataCorePlugin.GameData.NewData.$property"] = $v
        }
        Assert-Equal (Evaluate-Formula $timer.Bindings.Text.Formula.Expression) $case.Expected $timer.Name
    }
}
$status = $document.Screens[0].Items[1].Bindings.Text.Formula.Expression
Assert-Equal (Evaluate-Formula $status) 'CURRENT LAP' 'connected status'
foreach ($state in @(
    @{Running=$false; Game='IRacing'},
    @{Running=$false; Game='OtherGame'},
    @{Running=$true; Game='OtherGame'}
)) {
    $script:values['DataCorePlugin.GameRunning'] = $state.Running
    $script:values['DataCorePlugin.CurrentGame'] = $state.Game
    foreach ($timer in $timers) {
        Assert-Equal (Evaluate-Formula $timer.Bindings.Text.Formula.Expression) '--:--.---' 'inactive timer'
    }
    Assert-Equal (Evaluate-Formula $status) 'Waiting for iRacing' 'inactive status'
}
$script:values['DataCorePlugin.GameRunning'] = $true
$script:values['DataCorePlugin.CurrentGame'] = 'IRacing'
foreach ($property in $properties) { $script:values["DataCorePlugin.GameData.NewData.$property"] = [TimeSpan]::FromMilliseconds(80123) }
Assert-Equal (Evaluate-Formula $timers[0].Bindings.Text.Formula.Expression) '1:20.123' 'reconnected timer'
$script:values['DataCorePlugin.GameData.NewData.CurrentLapTime'] = [TimeSpan]::FromMilliseconds(31234)
$script:values['DataCorePlugin.GameData.NewData.LastLapTime'] = [TimeSpan]::FromMilliseconds(80123)
$script:values['DataCorePlugin.GameData.NewData.BestLapTime'] = [TimeSpan]::FromMilliseconds(78395)
foreach ($case in @(
    @{Index=0; Expected='0:31.234'},
    @{Index=1; Expected='1:20.123'},
    @{Index=2; Expected='1:18.395'}
)) {
    Assert-Equal (Evaluate-Formula $timers[$case.Index].Bindings.Text.Formula.Expression) $case.Expected 'independent timing binding'
}
foreach ($property in $properties) { $script:values["DataCorePlugin.GameData.NewData.$property"] = [TimeSpan]::Zero }
foreach ($timer in $timers) {
    Assert-Equal (Evaluate-Formula $timer.Bindings.Text.Formula.Expression) '--:--.---' 'session reset'
}
Write-Output 'PASS: NCalc formulas for sample times, minute rollover, null/zero, inactive game, and reconnection'
Write-Output 'NOTE: format/isnull/replace handlers use .NET equivalents; live SimHub property delivery remains untested'

Add-Type -AssemblyName System.IO.Compression.FileSystem
$package = [IO.Compression.ZipFile]::OpenRead((Join-Path $PSScriptRoot "$name.simhubdash"))
try {
    if ($package.Entries.Count -lt 3) { throw 'Incomplete package' }
    foreach ($suffix in @('.djson','.djson.metadata','.djson.ressources')) {
        if ($null -eq $package.GetEntry("$name/$name$suffix")) { throw "Missing $suffix" }
    }
} finally { $package.Dispose() }
Write-Output 'PASS: package directory structure matches the installed SimHub exporter'

if ($Live) {
    $liveData = Invoke-RestMethod -Uri 'http://localhost:8888/api/getgamedata' -TimeoutSec 5
    if (-not $liveData.GameRunning -or $liveData.GameName -ne 'IRacing') {
        throw 'Live iRacing telemetry is unavailable'
    }
    $script:values['DataCorePlugin.GameRunning'] = $liveData.GameRunning
    $script:values['DataCorePlugin.CurrentGame'] = $liveData.GameName
    foreach ($property in $properties) {
        $value = $liveData.NewData.$property
        $script:values["DataCorePlugin.GameData.NewData.$property"] = if ($null -eq $value) {
            $null
        } else { [TimeSpan]::Parse($value) }
    }
    Assert-Equal (Evaluate-Formula $status) 'CURRENT LAP' 'live connection gate'
    foreach ($timer in $timers) {
        Write-Output ("LIVE: {0} = {1}" -f $timer.Name, (Evaluate-Formula $timer.Bindings.Text.Formula.Expression))
    }
    Write-Output 'PASS: corrected formulas evaluated with live SimHub API telemetry'
    Write-Output 'NOTE: API GameName supplies the active game for this check; the actual CurrentGame dashboard property is confirmed by installed iRacing dashboards'
}
