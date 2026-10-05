param([string]$SimHubPath='C:\Program Files (x86)\SimHub')
$ErrorActionPreference='Stop'
$null=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$name='guysmiley222 - Advanced Lap Timer - retro'
$document=Get-Content -LiteralPath (Join-Path $PSScriptRoot "dashboard\$name\$name.djson") -Raw|ConvertFrom-Json
if ($document.BaseWidth -ne 320 -or $document.BaseHeight -ne 200 -or $document.Screens[0].Items.Count -lt 200) {throw 'Unexpected layout'}
$script:values=@{'DataCorePlugin.GameRunning'=$true;'DataCorePlugin.CurrentGame'='IRacing'}
$functionHandler=[NCalc.EvaluateFunctionHandler]{
    param($functionName,$functionArgs)
    $value=$functionArgs.Parameters[0].Evaluate()
    switch($functionName){
        'isnull' { $functionArgs.Result=if($null -eq $value){$functionArgs.Parameters[1].Evaluate()}else{$value} }
        'format' { $functionArgs.Result=if($null -eq $value){$null}else{$value.ToString($functionArgs.Parameters[1].Evaluate())} }
        'timespantoseconds' { $functionArgs.Result=([TimeSpan]$value).TotalSeconds }
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
        @{Delta=-0.245;Text='-000.245'}, @{Delta=0.318;Text='+000.318'},
        @{Delta=0.0;Text='+000.000'}, @{Delta=12.345;Text='+012.345'},
        @{Delta=599.999;Text='+599.999'}, @{Delta=-599.999;Text='-599.999'},
        @{Delta=60.0;Text='+060.000'}, @{Delta=$null;Text='---.---'}
    )){
        $script:values[$reference.Delta]=$case.Delta
        Assert-Equal (Evaluate-Item ($reference.Key+' split')) $case.Text
        Assert-Equal (Evaluate-Item ($reference.Key+' best')) '01:20.123'
    }
    $script:values[$reference.Delta]=0.318
    foreach($missingBest in @($null,[TimeSpan]::Zero)){
        $script:values[$reference.Best]=$missingBest
        Assert-Equal (Evaluate-Item ($reference.Key+' split')) '---.---'
        Assert-Equal (Evaluate-Item ($reference.Key+' best')) '--:--.---'
    }
}
$script:values['PersistantTrackerPlugin.SessionBest']=[TimeSpan]::FromMilliseconds(80123)
$script:values['PersistantTrackerPlugin.AllTimeBest']=[TimeSpan]::FromMilliseconds(78012)
$script:values['PersistantTrackerPlugin.SessionBestLiveDeltaSeconds']=-0.245
$script:values['PersistantTrackerPlugin.AllTimeBestLiveDeltaSeconds']=0.318
$script:values['DataCorePlugin.GameData.NewData.CurrentLapTime']=[TimeSpan]::FromMilliseconds(31234)
Assert-Equal (Evaluate-Item 'Current lap') '00:31.234'
Assert-Equal (Evaluate-Item 'session split') '-000.245'
Assert-Equal (Evaluate-Item 'alltime split') '+000.318'
Assert-Equal (Evaluate-Item 'session best') '01:20.123'
Assert-Equal (Evaluate-Item 'alltime best') '01:18.012'
foreach($state in @(@{Running=$false;Game='IRacing'},@{Running=$true;Game='OtherGame'})){
    $script:values['DataCorePlugin.GameRunning']=$state.Running
    $script:values['DataCorePlugin.CurrentGame']=$state.Game
    Assert-Equal (Evaluate-Item 'Connection status') 'Waiting for iRacing'
    Assert-Equal (Evaluate-Item 'session split') '---.---'
    Assert-Equal (Evaluate-Item 'alltime split') '---.---'
}
$script:values['DataCorePlugin.GameRunning']=$true
$script:values['DataCorePlugin.CurrentGame']='IRacing'
Assert-Equal (Evaluate-Item 'session split') '-000.245'
Write-Output 'PASS: independent reference laps, signed deltas, zero, missing references/deltas, connection states, and recovery'
Write-Output 'NOTE: live tracking-map availability and runtime display remain unverified; handlers use .NET equivalents'

$script:values['DataCorePlugin.GameData.NewData.CurrentLapTime']=[TimeSpan]::FromMilliseconds(3599999)
Assert-Equal (Evaluate-Item 'Current lap') '59:59.999'
$script:values['PersistantTrackerPlugin.SessionBest']=[TimeSpan]::FromMilliseconds(3599999)
$script:values['PersistantTrackerPlugin.AllTimeBest']=[TimeSpan]::FromMilliseconds(3599999)
Assert-Equal (Evaluate-Item 'session best') '59:59.999'
Assert-Equal (Evaluate-Item 'alltime best') '59:59.999'
Write-Output 'PASS: 59-minute laps and signed 9-minute splits'



$glyphs=@{'0'='abcdef';'1'='bc';'2'='abdeg';'3'='abcdg';'4'='bcfg';'5'='acdfg';'6'='acdefg';'7'='abc';'8'='abcdefg';'9'='abcdfg';'-'='g';'+'='gh';':'='ij';'.'='j';' '=''}
function Assert-Segments([string]$readout) {
    $expected=[string](Evaluate-Item $readout)
    if($readout.EndsWith(' split') -and $expected.Length -eq 7){$expected=' '+$expected}
    foreach($item in $document.Screens[0].Items | Where-Object {$_.Name.StartsWith($readout+' digit ') -and $_.Bindings.Opacity}) {
        $parts=$item.Name.Split(' ')
        $index=[int]$parts[-2]
        $segment=$parts[-1]
        $expr=New-Object NCalc.Expression($item.Bindings.Opacity.Formula.Expression)
        $expr.add_EvaluateFunction($functionHandler)
        $expr.add_EvaluateParameter($parameterHandler)
        $actual=$expr.Evaluate()
        $wanted=if($glyphs[[string]$expected[$index]].Contains($segment)){100}else{10}
        if($actual -ne $wanted){throw "Segment mismatch: $($item.Name), text=$expected, milliseconds=$milliseconds, delta=$delta, actual=$actual, wanted=$wanted"}
    }
}
$script:values['DataCorePlugin.GameRunning']=$true
$script:values['DataCorePlugin.CurrentGame']='IRacing'
foreach($milliseconds in @(1234,80123,754567,3599999,60000,59999,1000,0,$null)) {
    foreach($prop in @('DataCorePlugin.GameData.NewData.CurrentLapTime','PersistantTrackerPlugin.SessionBest','PersistantTrackerPlugin.AllTimeBest')) {
        $script:values[$prop]=if($null -eq $milliseconds){$null}else{[TimeSpan]::FromMilliseconds($milliseconds)}
    }
    foreach($delta in @(-599.999,-12.345,-0.245,0.0,0.318,12.345,599.999,$null)) {
        $script:values['PersistantTrackerPlugin.SessionBestLiveDeltaSeconds']=$delta
        $script:values['PersistantTrackerPlugin.AllTimeBestLiveDeltaSeconds']=$delta
        foreach($readout in @('Current lap','session best','alltime best','session split','alltime split')) { Assert-Segments $readout }
    }
}
$script:values['DataCorePlugin.GameRunning']=$false
foreach($readout in @('Current lap','session best','alltime best','session split','alltime split')) { Assert-Segments $readout }
Write-Output 'PASS: every segment matches formatted timing values, all digits, signs, rollovers, missing values, and disconnection'
