# Codex Cloud handoff; no automatic upload, commit, push or foreground actions.
param([string]$Task='', [string]$EnvironmentId='', [string]$Branch='main', [switch]$Submit, [switch]$DryRun)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$config=Get-Content -LiteralPath 'workflow/cloud/codex-cloud.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $EnvironmentId) { $EnvironmentId=$config.environment_id }
if (-not $Task) { $Task=$config.default_task }
Write-Host ('Codex Cloud: '+$config.web_url)
Write-Host ('GitHub: '+$config.repository)
Write-Host ('Branch: '+$Branch)
if ($DryRun) { Write-Host 'DRY RUN: no network, file writes, submission, commit or push.'; Write-Host $Task; return }
if (-not $Submit) {
    Write-Host 'Sign in with ChatGPT, connect GitHub, choose Work in > Cloud and select the repository.'
    Write-Host 'No task submitted. Local uncommitted changes are not uploaded.'
    Write-Host ('Task to paste: '+$Task)
    Write-Host 'CLI: add -Submit -EnvironmentId <verified repository environment ID> -Task <task>.'
    return
}
if (-not $EnvironmentId) { throw 'Connect GitHub and configure a verified repository environment first.' }
if (@(git status --porcelain --untracked-files=no).Count -gt 0) { throw 'Review and explicitly sync local tracked changes before submitting cloud work.' }
$remote=git remote get-url origin
if ($LASTEXITCODE -ne 0 -or $remote.Trim() -ne $config.remote_url) { throw 'Unexpected GitHub origin.' }
& codex cloud exec --env $EnvironmentId --branch $Branch --attempts 1 $Task
if ($LASTEXITCODE -ne 0) { throw 'Cloud submission failed; check authentication, environment and network.' }
