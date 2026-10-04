param([string]$SimHubPath='C:\Program Files (x86)\SimHub')
$ErrorActionPreference='Stop'
$null=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$name='guysmiley222 - Advanced Lap Timer'
$document=Get-Content -LiteralPath (Join-Path $PSScriptRoot "dashboard\$name\$name.djson") -Raw|ConvertFrom-Json
if ($document.BaseWidth -ne 320 -or $document.BaseHeight -ne 200 -or $document.Screens[0].Items.Count -ne 11) {throw 'Unexpected layout'}
$script:values=@{'DataCorePlugin.GameRunning'=$true;'DataCorePlugin.CurrentGame'='IRacing'}
$functionHandler=[NCalc.EvaluateFunctionHandler]{
    param($functionName,$functionArgs)
    $value=$functionArgs.Parameters[0].Evaluate()
    switch($functionName){
        'isnull' { $functionArgs.Result=if($null -eq $value){$functionArgs.Parameters[1].Evaluate()}else{$value} }
        'format' { $functionArgs.Result=if($null -eq $value){$null}else{$value.ToString($functionArgs.Parameters[1].Evaluate())} }
        'replace' { $functionArgs.Result=([string]$value).Replace([string]$functionArgs.Parameters[1].Evaluate(),[string]$functionArgs.Parameters[2].Evaluate()) }
    }
}
$parameterHandler=[NCalc.EvaluateParameterHandler]{param($parameterName,$parameterArgs);$parameterArgs.Result=$script:values[$parameterName]}
function Evaluate-Item([string]$name){
    $item=$document.Screens[0].Items|Where-Object {$_.Name -eq $name}
    $expression=New-Object NCalc.Expression($item.Bindings.Text.Formula.Expression)
    $expression.add_EvaluateFunction($functionHandler)
    $expression.add_EvaluateParameter($parameterHandler)
    return $expression.Evaluate()
}
function Assert-Equal($actual,$expected){if($actual -ne $expected){throw "Expected '$expected', got '$actual'"}}
foreach($reference in @(
    @{Key='session';Best='PersistantTrackerPlugin.SessionBest';Delta='PersistantTrackerPlugin.SessionBestLiveDeltaSeconds'},
    @{Key='alltime';Best='PersistantTrackerPlugin.AllTimeBest';Delta='PersistantTrackerPlugin.AllTimeBestLiveDeltaSeconds'}
)){
    $script:values[$reference.Best]=[TimeSpan]::FromMilliseconds(80123)
    foreach($case in @(
        @{Delta=-0.245;Text='-0.245'}, @{Delta=0.318;Text='+0.318'},
        @{Delta=0.0;Text='+0.000'}, @{Delta=12.345;Text='+12.345'},
        @{Delta=$null;Text='--.---'}
    )){
        $script:values[$reference.Delta]=$case.Delta
        Assert-Equal (Evaluate-Item ($reference.Key+' split')) $case.Text
        Assert-Equal (Evaluate-Item ($reference.Key+' best')) '1:20.123'
    }
    $script:values[$reference.Delta]=0.318
    foreach($missingBest in @($null,[TimeSpan]::Zero)){
        $script:values[$reference.Best]=$missingBest
        Assert-Equal (Evaluate-Item ($reference.Key+' split')) '--.---'
        Assert-Equal (Evaluate-Item ($reference.Key+' best')) '--:--.---'
    }
}
$script:values['PersistantTrackerPlugin.SessionBest']=[TimeSpan]::FromMilliseconds(80123)
$script:values['PersistantTrackerPlugin.AllTimeBest']=[TimeSpan]::FromMilliseconds(78012)
$script:values['PersistantTrackerPlugin.SessionBestLiveDeltaSeconds']=-0.245
$script:values['PersistantTrackerPlugin.AllTimeBestLiveDeltaSeconds']=0.318
$script:values['DataCorePlugin.GameData.NewData.CurrentLapTime']=[TimeSpan]::FromMilliseconds(31234)
Assert-Equal (Evaluate-Item 'Current lap') '0:31.234'
Assert-Equal (Evaluate-Item 'session split') '-0.245'
Assert-Equal (Evaluate-Item 'alltime split') '+0.318'
Assert-Equal (Evaluate-Item 'session best') '1:20.123'
Assert-Equal (Evaluate-Item 'alltime best') '1:18.012'
foreach($state in @(@{Running=$false;Game='IRacing'},@{Running=$true;Game='OtherGame'})){
    $script:values['DataCorePlugin.GameRunning']=$state.Running
    $script:values['DataCorePlugin.CurrentGame']=$state.Game
    Assert-Equal (Evaluate-Item 'Connection status') 'Waiting for iRacing'
    Assert-Equal (Evaluate-Item 'session split') '--.---'
    Assert-Equal (Evaluate-Item 'alltime split') '--.---'
}
$script:values['DataCorePlugin.GameRunning']=$true
$script:values['DataCorePlugin.CurrentGame']='IRacing'
Assert-Equal (Evaluate-Item 'session split') '-0.245'
Write-Output 'PASS: independent reference laps, signed deltas, zero, missing references/deltas, connection states, and recovery'
Write-Output 'NOTE: live tracking-map availability and runtime display remain unverified; handlers use .NET equivalents'
