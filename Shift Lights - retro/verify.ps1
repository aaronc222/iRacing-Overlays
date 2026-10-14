# Run the standard Shift Lights checks against this folder, including seven-segment decoding.
& (Join-Path (Split-Path $PSScriptRoot) 'Shift Lights\verify.ps1') -OverlayRoot $PSScriptRoot -Unlit 10
