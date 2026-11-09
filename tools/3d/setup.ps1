param([string]$Python = 'python')
$ErrorActionPreference='Stop'
$ProjectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$ToolsRoot=Join-Path $ProjectRoot 'tools/3d'
$Source=Join-Path $ToolsRoot 'blender-mcp'
$Revision='dbbf836ad4b1025f14a2b3b504c43903f39e0b04'
if(-not(Test-Path (Join-Path $Source '.git'))){git clone https://projects.blender.org/lab/blender_mcp.git $Source}
git -C $Source checkout $Revision
if(-not(Test-Path (Join-Path $ToolsRoot '.venv/Scripts/python.exe'))){& $Python -m venv (Join-Path $ToolsRoot '.venv')}
& (Join-Path $ToolsRoot '.venv/Scripts/python.exe') -m pip install bpy==5.2.3 (Join-Path $Source 'mcp')
if($LASTEXITCODE -ne 0){throw 'Blender tooling installation failed'}
