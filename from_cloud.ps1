# Codex Cloud results: preview by default, apply only on explicit request.
param([string]$TaskId='', [switch]$Apply, [switch]$DryRun)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if ($DryRun) { Write-Host 'DRY RUN: no network, file writes, commit, pull or merge.'; return }
if (-not $TaskId) { & codex cloud list; if ($LASTEXITCODE -ne 0) { throw 'Cannot list cloud tasks.' }; Write-Host 'Pass -TaskId <id> to preview; add -Apply to apply the patch.'; return }
if (-not $Apply) { & codex cloud diff $TaskId; if ($LASTEXITCODE -ne 0) { throw 'Cannot read cloud diff.' }; return }
if (@(git status --porcelain).Count -gt 0) { throw 'Working tree is not clean. Preserve local work before applying the patch.' }
& codex cloud apply $TaskId
if ($LASTEXITCODE -ne 0) { throw 'Patch application failed. Inspect conflicts; no automatic merge or reset is performed.' }
