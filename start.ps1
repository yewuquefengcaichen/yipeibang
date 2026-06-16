$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerModule = "server_fastapi:app"
$PidPath = Join-Path $ProjectRoot "server.pid"
$LogPath = Join-Path $ProjectRoot "server.log"
$ErrPath = Join-Path $ProjectRoot "server.err.log"

Set-Location $ProjectRoot

if (Test-Path $PidPath) {
    $oldPid = Get-Content $PidPath -ErrorAction SilentlyContinue
    if ($oldPid) {
        $oldProcess = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
        if ($oldProcess) {
            Stop-Process -Id $oldProcess.Id -Force
            Start-Sleep -Milliseconds 300
        }
    }
}

$Args = @("-m", "uvicorn", $ServerModule, "--host", "127.0.0.1", "--port", "8120")
$Process = Start-Process -FilePath "python" -ArgumentList $Args -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $LogPath -RedirectStandardError $ErrPath
$Process.Id | Set-Content -Path $PidPath -Encoding ASCII

Start-Sleep -Milliseconds 900

Write-Host "医陪帮 Python 后端已启动"
Write-Host "默认地址: http://127.0.0.1:8120/"
Write-Host "当前使用 FastAPI 流式智能体服务。"
Write-Host "PID: $($Process.Id)"
Write-Host "目录: $ProjectRoot"
