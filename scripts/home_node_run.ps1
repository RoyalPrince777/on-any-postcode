$ErrorActionPreference = "Stop"
$RepoDir = if ($env:OAP_HOME_REPO) { $env:OAP_HOME_REPO } else { Join-Path $HOME "on-any-postcode" }
$VenvPython = Join-Path $RepoDir ".venv\Scripts\python.exe"
$EnvFile = Join-Path $HOME ".config\oap\home-node.ps1"
if (-not (Test-Path (Join-Path $RepoDir ".git"))) { throw "Home Node repo missing: $RepoDir" }
if (-not (Test-Path $VenvPython)) { throw "Home Node Python missing: $VenvPython" }
if (Test-Path $EnvFile) { . $EnvFile }
Set-Location $RepoDir
$env:OAP_HOME_REPO = $RepoDir
try { $env:OAP_ENV_REVISION = (git rev-parse --short=12 HEAD).Trim() } catch { $env:OAP_ENV_REVISION = "device-local" }
& $VenvPython (Join-Path $RepoDir "scripts\oap_home_node_supervisor.py")
exit $LASTEXITCODE
