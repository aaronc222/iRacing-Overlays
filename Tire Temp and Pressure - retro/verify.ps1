param([string]$SimHubPath='C:\Program Files (x86)\SimHub')
$ErrorActionPreference='Stop'
$null=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'NCalc.dll'))
$null=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'Newtonsoft.Json.dll'))
$assembly=[Reflection.Assembly]::LoadFrom((Join-Path $SimHubPath 'SimHub.Plugins.dll'))
$name='guysmiley222 - '+(Split-Path $PSScriptRoot -Leaf)
$document=Get-Content -LiteralPath (Join-Path $PSScriptRoot "dashboard\$name\$name.djson") -Raw|ConvertFrom-Json
$script:values=@{'DataCorePlugin.GameRunning'=$true;'DataCorePlugin.CurrentGame'='IRacing'}
$functions=[NCalc.EvaluateFunctionHandler]{
 param($n,$a)
 if($n -eq 'isnull'){$v=$a.Parameters[0].Evaluate();$a.Result=if($null -eq $v){$a.Parameters[1].Evaluate()}else{$v}}
 if($n -eq 'format'){$a.Result=$a.Parameters[0].Evaluate().ToString($a.Parameters[1].Evaluate(),[Globalization.CultureInfo]::InvariantCulture)}
}
$parameters=[NCalc.EvaluateParameterHandler]{param($n,$a);$a.Result=$script:values[$n]}
function Eval($formula){$e=New-Object NCalc.Expression($formula);$e.add_EvaluateFunction($functions);$e.add_EvaluateParameter($parameters);return $e.Evaluate()}
function Check($item,$expected){$actual=Eval $item.Bindings.Text.Formula.Expression;if($actual -ne $expected){throw "$($item.Name): expected $expected got $actual"}}
foreach($c in @('LF','RF','LR','RR')){
 $p='DataCorePlugin.GameRawData.Telemetry.'+$c
 $temp=$document.Screens[0].Items|Where-Object Name -eq ($c+' temperature')
 $pressure=$document.Screens[0].Items|Where-Object Name -eq ($c+' pressure')
 foreach($s in @('L','M','R')){$script:values[$p+'tempC'+$s]=[double]80}
 $script:values[$p+'tempCM']=[double]86
 $script:values[$p+'coldPressure']=[double](23.5*6.894757293168)
 Check $temp '082';Check $pressure '23.5'
 foreach($item in $document.Screens[0].Items|Where-Object {$_.Name -like "$c*" -and $null -ne $_.Bindings.Opacity}){
  $v=Eval $item.Bindings.Opacity.Formula.Expression
  if($v -notin @(10,100)){throw 'Invalid segment opacity'}
 }
 $script:values[$p+'tempCL']=$null;Check $temp '---'
 foreach($s in @('L','M','R')){$script:values[$p+'tempC'+$s]=[double]0};Check $temp '000'
 $script:values[$p+'coldPressure']=[double]0;Check $pressure '---'
 $script:values[$p+'coldPressure']=$null;Check $pressure '---'
 foreach($s in @('L','M','R')){$script:values[$p+'tempC'+$s]=[double]1000};Check $temp '---'
 $script:values[$p+'coldPressure']=[double]800;Check $pressure '---'
 foreach($s in @('L','M','R')){$script:values[$p+'tempC'+$s]=[double]80}
 $script:values[$p+'coldPressure']=[double](23.5*6.894757293168)
 foreach($state in @(@{Running=$false;Game='IRacing'},@{Running=$true;Game='Other'})){
  $script:values['DataCorePlugin.GameRunning']=$state.Running;$script:values['DataCorePlugin.CurrentGame']=$state.Game
  Check $temp '---';Check $pressure '---'
 }
 $script:values['DataCorePlugin.GameRunning']=$true;$script:values['DataCorePlugin.CurrentGame']='IRacing'
 Check $temp '080';Check $pressure '23.5'
}
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
    if($ids.ContainsKey($data.Id)){throw 'Duplicate identity'};$ids[$data.Id]=$true
    foreach($item in $data.Screens[0].Items){
     if($item.Bindings.TextColor -or $item.Bindings.BackgroundColor){throw 'Uncompiled color'}
     if($item.Left -lt 0 -or $item.Top -lt 0 -or ($item.Left+$item.Width) -gt 320 -or ($item.Top+$item.Height) -gt 240){throw 'Item outside panel'}
    }
   }
  }
  if(@($zip.Entries|Where-Object {$_.FullName -match '\.png$'}).Count -ne 2){throw 'Missing thumbnails'}
 }finally{$zip.Dispose()}
}
if($ids.Count -ne 6){throw 'Expected six themes'}
Write-Output 'PASS: averaging, PSI conversion, missing/zero/out-of-range data, disconnect/recovery, retro opacity expressions, six model-loaded packages, identities, bounds and thumbnails'
