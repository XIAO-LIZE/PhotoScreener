[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-Location $PSScriptRoot

$python = "$PSScriptRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host ""
    Write-Host "  [ERROR] Not installed yet / 尚未安装!" -ForegroundColor Red
    Write-Host "  Run: .\setup.ps1 first / 请先运行: .\setup.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Press Enter / 按回车退出"
    exit 1
}

Write-Host ""
Write-Host "  Photo Screener / 照片筛选器" -ForegroundColor Cyan
Write-Host "  Browser / 浏览器: http://127.0.0.1:7860" -ForegroundColor White
Write-Host "  Ctrl+C to stop / 按 Ctrl+C 停止" -ForegroundColor Gray
Write-Host ""

& $python "$PSScriptRoot\main.py"

Write-Host ""
Write-Host "  App stopped / 程序已退出" -ForegroundColor Gray
Read-Host "  Press Enter / 按回车退出"
