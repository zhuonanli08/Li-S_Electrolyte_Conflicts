# 不用打命令：双击同一文件夹里的「双击同步回本机.bat」即可。
# 作用：把 GitHub 上云端做好的最新进度拉回本机。本机若有没保存的改动，先自动存一份快照，不会丢。
param([switch]$DryRun)

Set-Location $PSScriptRoot

Write-Host "1/3 保存本机改动（有的话）..."
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -q -m ("本机进度快照 " + (Get-Date -Format 'yyyy-MM-dd HH:mm')) | Out-Null
}
$before = git rev-parse HEAD

Write-Host "2/3 从 GitHub 下载云端进度..."
if ($DryRun) { Write-Host "（测试模式：不下载）"; exit 0 }
git pull -q --no-rebase origin main
if ($LASTEXITCODE -ne 0) {
    git merge --abort 2>$null
    Write-Host "同步没完成：本机和云端改了同一处，或网络不通。" -ForegroundColor Red
    Write-Host "先确认 Clash 开着再双击一次；还不行就双击「双击上云.bat」，让云端来合并。" -ForegroundColor Red
    exit 1
}

Write-Host "3/3 完成。这次拉回来的更新：" -ForegroundColor Green
git log --oneline "$before..HEAD"
Write-Host ""
Write-Host "最新进度见 进度.md；方案见 课题二_锂硫电解液矛盾归因_课题方案.md。这个窗口可以关掉。"
