# 強制停止 SinoPac 程式
Write-Host "正在查找 SinoPac-new.py 進程..." -ForegroundColor Yellow

$processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*SinoPac-new.py*" -or
    $_.CommandLine -like "*SinoPac-new.py*"
}

if ($processes) {
    Write-Host "找到 $($processes.Count) 個相關進程" -ForegroundColor Green
    foreach ($proc in $processes) {
        Write-Host "停止進程: PID $($proc.Id)" -ForegroundColor Cyan
        Stop-Process -Id $proc.Id -Force
    }
    Write-Host "✓ 所有進程已停止" -ForegroundColor Green
} else {
    # 如果找不到特定的，停止所有 python 進程
    $allPython = Get-Process python -ErrorAction SilentlyContinue
    if ($allPython) {
        Write-Host "找到 $($allPython.Count) 個 Python 進程" -ForegroundColor Yellow
        Write-Host "是否停止所有 Python 進程? (Y/N)" -ForegroundColor Yellow
        $confirm = Read-Host
        if ($confirm -eq 'Y' -or $confirm -eq 'y') {
            foreach ($proc in $allPython) {
                Write-Host "停止進程: PID $($proc.Id)" -ForegroundColor Cyan
                Stop-Process -Id $proc.Id -Force
            }
            Write-Host "✓ 所有 Python 進程已停止" -ForegroundColor Green
        } else {
            Write-Host "已取消" -ForegroundColor Gray
        }
    } else {
        Write-Host "沒有找到運行中的 Python 進程" -ForegroundColor Gray
    }
}
