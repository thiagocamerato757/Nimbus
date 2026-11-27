$ErrorActionPreference = 'Stop'
$browser = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$profile = Join-Path $env:TEMP ('nimbus-smoke-' + [guid]::NewGuid().ToString())
$dom = Join-Path $env:TEMP 'nimbus-6-windows-dom.html'
$err = Join-Path $env:TEMP 'nimbus-6-windows-edge.stderr'
Write-Output ('UTC ' + [DateTime]::UtcNow.ToString('o'))
Write-Output ('Edge ' + (Get-Item $browser).VersionInfo.ProductVersion)
Write-Output 'Windows Edge headless -> http://localhost:5173 -> WSL2 Vite -> loopback FastAPI'
$arguments = @('--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', "--user-data-dir=$profile", '--virtual-time-budget=10000', '--dump-dom', 'http://localhost:5173')
$process = Start-Process -FilePath $browser -ArgumentList $arguments -Wait -PassThru -RedirectStandardOutput $dom -RedirectStandardError $err
Write-Output ('Process exit: ' + $process.ExitCode)
$html = Get-Content -Raw $dom
Write-Output $html
if ($html -notmatch 'League of Legends' -or $html -notmatch 'Create Series' -or $html -match 'Could not reach Nimbus') { throw 'Rendered API-backed application not found' }
Write-Output 'PASS: Windows browser rendered the React application and API-loaded League of Legends profile.'
