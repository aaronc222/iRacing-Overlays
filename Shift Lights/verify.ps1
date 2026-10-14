param([string]$SimHubPath='C:\Program Files (x86)\SimHub')
$ErrorActionPreference='Stop'
$null=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$null=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'Newtonsoft.Json.dll'))
$assembly=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'SimHub.Plugins.dll'))
$name='guysmiley222 - '+(Split-Path $PSScriptRoot -Leaf)
$document=Get-Content -LiteralPath (Join-Path $PSScriptRoot "dashboard\$name\$name.djson") -Raw|ConvertFrom-Json
$items=$document.Screens[0].Items
$d='DataCorePlugin.GameData.NewData.'
$script:blink=$true
$script:values=@{}
function Reset{
 $script:values=@{'DataCorePlugin.GameRunning'=$true;'DataCorePlugin.CurrentGame'='IRacing'
  ($d+'Gear')='4';($d+'Rpms')=[double]7420;($d+'Throttle')=[double]58.4
  ($d+'CarSettings_CurrentGearRedLineRPM')=[double]7900;($d+'CarSettings_RedLineRPM')=[double]8100}
}
# SimHub's blink() alternates; the check pins both phases explicitly.
$functions=[NCalc.EvaluateFunctionHandler]{
 param($n,$a)
 if($n -eq 'isnull'){$v=$a.Parameters[0].Evaluate();$a.Result=if($null -eq $v){$a.Parameters[1].Evaluate()}else{$v}}
 if($n -eq 'format'){$a.Result=$a.Parameters[0].Evaluate().ToString($a.Parameters[1].Evaluate(),[Globalization.CultureInfo]::InvariantCulture)}
 if($n -eq 'blink'){$a.Result=$script:blink}
}
$parameters=[NCalc.EvaluateParameterHandler]{param($n,$a);$a.Result=$script:values[$n]}
function Eval($formula){$e=New-Object NCalc.Expression($formula);$e.add_EvaluateFunction($functions);$e.add_EvaluateParameter($parameters);return $e.Evaluate()}
function Item($n){$items|Where-Object Name -eq $n}
function Check($n,$expected){$actual=Eval (Item $n).Bindings.Text.Formula.Expression;if($actual -ne $expected){throw "${n}: expected $expected got $actual"}}
$leds=@(1..10|ForEach-Object{Item "LED $_"})
if($leds.Count -ne 10){throw 'Expected ten LEDs'}
function Lit{
 $levels=@($leds|ForEach-Object{Eval $_.Bindings.Opacity.Formula.Expression})
 if(@($levels|Where-Object{$_ -notin @(15,100)}).Count){throw "Invalid LED opacity: $levels"}
 $lit=@($levels|Where-Object{$_ -eq 100}).Count
 # Lit LEDs must always fill from the left with no gaps.
 if($lit -gt 0 -and @($levels[0..($lit-1)] -ne 100).Count){throw "LED gap: $levels"}
 return $lit
}
function Expect($count,$label){$actual=Lit;if($actual -ne $count){throw "${label}: expected $count lit got $actual"}}

Reset
Check 'Gear' '4';Check 'RPM' '07420';Check 'Throttle' '058';Check 'Redline' '07900';Check 'Connection status' 'RPM'
Expect 8 'sample 7420/7900'
$script:values[$d+'Rpms']=[double]0;Expect 0 'idle'
for($i=0;$i -lt 10;$i++){
 $threshold=[Math]::Round(7900*(0.70+0.03*$i))
 $script:values[$d+'Rpms']=[double]($threshold+1);Expect ($i+1) "just above LED $($i+1)"
 $script:values[$d+'Rpms']=[double]($threshold-2);Expect $i "just below LED $($i+1)"
}
foreach($rpm in @(7900,9000)){
 $script:values[$d+'Rpms']=[double]$rpm
 $script:blink=$true;Expect 10 "flash on at $rpm"
 $script:blink=$false;Expect 0 "flash off at $rpm"
}
$script:blink=$true
# Per-gear redline missing or zero falls back to the car redline.
foreach($perGear in @($null,[double]0)){
 Reset;$script:values[$d+'CarSettings_CurrentGearRedLineRPM']=$perGear
 Check 'Redline' '08100';$script:values[$d+'Rpms']=[double]8000;Expect 10 'fallback redline'
}
# No known redline: lights stay dark rather than guessing.
Reset;$script:values[$d+'CarSettings_CurrentGearRedLineRPM']=[double]0;$script:values[$d+'CarSettings_RedLineRPM']=$null
Check 'Redline' '-----';$script:values[$d+'Rpms']=[double]12000;Expect 0 'unknown redline'
Reset;foreach($p in @('Gear','Rpms','Throttle')){$script:values[$d+$p]=$null}
Check 'Gear' '-';Check 'RPM' '-----';Check 'Throttle' '---';Expect 0 'missing RPM'
Reset;$script:values[$d+'Gear']='N';$script:values[$d+'Throttle']=[double]100;Check 'Gear' 'N';Check 'Throttle' '100'
$script:values[$d+'Throttle']=[double]150;Check 'Throttle' '---'
$script:values[$d+'Rpms']=[double]100000;Check 'RPM' '-----'
foreach($state in @(@{Running=$false;Game='IRacing'},@{Running=$true;Game='Other'})){
 Reset;$script:values['DataCorePlugin.GameRunning']=$state.Running;$script:values['DataCorePlugin.CurrentGame']=$state.Game
 Check 'Gear' '-';Check 'RPM' '-----';Check 'Throttle' '---';Check 'Redline' '-----';Check 'Connection status' 'Waiting for iRacing'
 $script:values[$d+'Rpms']=[double]9000;Expect 0 'disconnected at redline'
}
Reset;Check 'RPM' '07420';Expect 8 'recovery'

Add-Type -AssemblyName System.IO.Compression.FileSystem
$settings=New-Object Newtonsoft.Json.JsonSerializerSettings
$settings.TypeNameHandling=[Newtonsoft.Json.TypeNameHandling]::Auto
$ids=@{}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'themed') -Filter '*.simhubdash'){
 $zip=[IO.Compression.ZipFile]::OpenRead($file.FullName)
 try{
  foreach($entry in $zip.Entries|Where-Object {$_.FullName -match '\.djson(\.metadata)?$'}){
   $reader=New-Object IO.StreamReader($entry.Open());try{$json=$reader.ReadToEnd()}finally{$reader.Dispose()}
   $type=if($entry.FullName.EndsWith('.metadata')){'DashboardMetadata'}else{'Dashboard'}
   $previous=[Environment]::CurrentDirectory
   try{[Environment]::CurrentDirectory=$SimHubPath;$model=[Newtonsoft.Json.JsonConvert]::DeserializeObject($json,$assembly.GetType("SimHub.Plugins.OutputPlugins.GraphicalDash.$type"),$settings)}finally{[Environment]::CurrentDirectory=$previous}
   if($null -eq $model){throw 'Model load failed'}
   if($type -eq 'Dashboard'){
    $data=$json|ConvertFrom-Json
    if($ids.ContainsKey($data.Id) -or $data.Id -eq $document.Id){throw 'Duplicate identity'};$ids[$data.Id]=$true
    foreach($item in $data.Screens[0].Items){
     if($item.Bindings.TextColor -or $item.Bindings.BackgroundColor){throw 'Uncompiled color'}
     if($item.Left -lt 0 -or $item.Top -lt 0 -or ($item.Left+$item.Width) -gt 320 -or ($item.Top+$item.Height) -gt 150){throw "Item outside panel: $($item.Name)"}
    }
    $compiledLeds=@($data.Screens[0].Items|Where-Object {$_.Name -like 'LED *'})
    for($i=0;$i -lt 10;$i++){
     if($compiledLeds[$i].Bindings.Opacity.Formula.Expression -ne $leds[$i].Bindings.Opacity.Formula.Expression){throw 'LED logic changed by theme compile'}
    }
   }
  }
  if(@($zip.Entries|Where-Object {$_.FullName -match '\.png$'}).Count -ne 2){throw 'Missing thumbnails'}
 }finally{$zip.Dispose()}
}
if($ids.Count -ne 6){throw 'Expected six themes'}
Write-Output 'PASS: LED thresholds and fill order, redline flash phases, per-gear/car redline fallback, unknown redline, missing/out-of-range data, disconnect/recovery, six model-loaded packages, identities, bounds and thumbnails'
