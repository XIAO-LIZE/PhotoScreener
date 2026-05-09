# Photo Screener - Setup / 照片筛选器 - 安装向导
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Set-Location $PSScriptRoot

# ---- Pretty print helpers ----
function Show-Step  { param($msg) Write-Host ""; Write-Host "  >>> $msg" -ForegroundColor Cyan }
function Show-OK    { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Show-Warn  { param($msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Show-Err   { param($msg) Write-Host "  [XX] $msg" -ForegroundColor Red }
function Show-Info  { param($msg) Write-Host "  $msg" -ForegroundColor Gray }
function Show-Bar   { Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkCyan }

# ---- Custom pip with Chinese ETA ----
function Invoke-Pip {
    param(
        [string]$VenvPip,
        [string]$Arguments
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $VenvPip
    $psi.Arguments = $Arguments
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
    $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8

    $proc = [System.Diagnostics.Process]::Start($psi)

    # Read stdout + stderr interleaved
    while (-not $proc.StandardOutput.EndOfStream) {
        $line = $proc.StandardOutput.ReadLine()
        $line = $line -replace 'eta (\d+:\d+:\d+)', '剩余 $1'
        $line = $line -replace 'eta (\d+:\d+)', '剩余 $1'
        Write-Host $line
    }
    # Flush remaining
    $rest = $proc.StandardOutput.ReadToEnd()
    if ($rest) {
        $rest = $rest -replace 'eta (\d+:\d+:\d+)', '剩余 $1'
        $rest = $rest -replace 'eta (\d+:\d+)', '剩余 $1'
        Write-Host $rest
    }
    # Show errors
    $err = $proc.StandardError.ReadToEnd()
    if ($err) {
        $err = $err -replace 'eta (\d+:\d+:\d+)', '剩余 $1'
        $err = $err -replace 'eta (\d+:\d+)', '剩余 $1'
        Write-Host $err
    }

    $proc.WaitForExit()
    return $proc.ExitCode
}

# ---- Header ----
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     Photo Screener - Setup                ║" -ForegroundColor Cyan
Write-Host "  ║     照片筛选器 - 安装向导                  ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ---- Region Selection ----
Write-Host "  Select download source / 选择下载源:" -ForegroundColor Yellow
Write-Host ""
Write-Host "    [1]  China / 中国 (Tsinghua mirror / 清华镜像)" -ForegroundColor White
Write-Host "    [2]  Global / 海外 (Official PyPI + PyTorch)" -ForegroundColor White
Write-Host ""
$region = Read-Host "  Choice / 选择 [1-2]"

if ($region -eq "1") {
    $PIP_INDEX   = "https://pypi.tuna.tsinghua.edu.cn/simple"
    $sourceLabel = "Tsinghua / 清华镜像"
} else {
    $PIP_INDEX   = "https://pypi.org/simple"
    $sourceLabel = "Official PyPI"
}

$TORCH_CU128 = "https://download.pytorch.org/whl/nightly/cu128"
$TORCH_CU124 = "https://download.pytorch.org/whl/nightly/cu124"

Write-Host ""
Show-Bar
Write-Host "  Pip Source / Pip 源:    $sourceLabel" -ForegroundColor Green
Write-Host "  PyTorch CUDA / PyTorch: Official / 官方源" -ForegroundColor Green
Show-Bar

# ---- Step 1: Python ----
Show-Step "[1/4] Python / Python 检查"
$pyVer = & python --version 2>&1
if (-not $pyVer) {
    Show-Err "Python not found / 未找到 Python!"
    Show-Info "Download / 下载: https://www.python.org/downloads/"
    Show-Info "Check 'Add to PATH' / 安装时勾选 'Add Python to PATH'"
    Read-Host "  Press Enter / 按回车退出"
    exit 1
}
Show-OK "Found / 找到: $pyVer"

# ---- Step 2: venv ----
Show-Step "[2/4] Virtual Environment / 虚拟环境"
if (Test-Path ".venv\Scripts\pip.exe") {
    # Check if pip is actually working
    $pipCheck = & "$PSScriptRoot\.venv\Scripts\python.exe" -m pip --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Show-Warn "venv broken / 虚拟环境已损坏，重建..."
        Remove-Item -Recurse -Force ".venv"
    } else {
        Show-OK "venv exists / 已存在，复用"
    }
}
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Show-Info "Creating new venv / 创建新虚拟环境 ..."
    & python -m venv .venv
    Show-OK "Created / 已创建 .venv"
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$venvPip    = Join-Path $PSScriptRoot ".venv\Scripts\pip.exe"

Show-Info "Upgrading pip / 升级 pip ..."
Invoke-Pip -VenvPip $venvPython -Arguments "-m pip install --upgrade pip -i $PIP_INDEX --progress-bar on"
Show-OK "pip upgraded / pip 升级完成"

# ---- Step 3: PyTorch ----
Show-Step "[3/4] PyTorch / PyTorch 安装"

$hasGpu = $false
try { nvidia-smi 2>&1 | Out-Null; $hasGpu = $true } catch {}

if ($hasGpu) {
    Show-OK "GPU detected / 检测到显卡:"
    $gpuName = nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
    Write-Host "    >>> $gpuName" -ForegroundColor Green

    $torchOk = $false

    Write-Host ""
    Show-Info "Try 1/3: Nightly + CUDA 12.8 (~900MB)"
    Show-Bar
    $code = Invoke-Pip -VenvPip $venvPip -Arguments "install --pre torch torchvision --index-url $TORCH_CU128 --progress-bar on"
    if ($code -eq 0) { $torchOk = $true }

    if (-not $torchOk) {
        Write-Host ""
        Show-Warn "Try 1 failed / 失败, trying Try 2/3 ..."
        Show-Info "Try 2/3: Nightly + CUDA 12.4"
        Show-Bar
        $code = Invoke-Pip -VenvPip $venvPip -Arguments "install --pre torch torchvision --index-url $TORCH_CU124 --progress-bar on"
        if ($code -eq 0) { $torchOk = $true }
    }

    if (-not $torchOk) {
        Write-Host ""
        Show-Warn "Try 2 failed / 失败, trying Try 3/3 ..."
        Show-Info "Try 3/3: Stable (CPU-only / 只有 CPU 版)"
        Show-Bar
        $code = Invoke-Pip -VenvPip $venvPip -Arguments "install torch torchvision -i $PIP_INDEX --progress-bar on"
        if ($code -eq 0) { $torchOk = $true }
    }

    if ($torchOk) {
        Show-OK "PyTorch installed / 安装成功"
    } else {
        Show-Err "All methods failed / 所有方式均失败"
        Read-Host "  Press Enter / 按回车退出"
        exit 1
    }
} else {
    Show-Warn "No GPU / 未检测到显卡"
    Show-Info "Installing CPU version / 安装 CPU 版 ..."
    Show-Bar
    Invoke-Pip -VenvPip $venvPip -Arguments "install torch torchvision -i $PIP_INDEX --progress-bar on"
    Show-OK "CPU PyTorch installed / 安装成功"
}

# ---- Step 4: Other deps ----
Write-Host ""
Show-Step "[4/4] Dependencies / 其他依赖"
Show-Bar
$code = Invoke-Pip -VenvPip $venvPip -Arguments "install -i $PIP_INDEX -r requirements.txt --progress-bar on"
if ($code -ne 0) {
    Show-Warn "Some packages failed, retrying / 部分失败，重试 ..."
    Show-Bar
    Invoke-Pip -VenvPip $venvPip -Arguments "install -r requirements.txt --progress-bar on"
}
Show-OK "Dependencies installed / 依赖安装完成"

# ---- Verify ----
Write-Host ""
Show-Bar
Write-Host "  Verification / 验证" -ForegroundColor Cyan
Show-Bar

& $venvPython -c @"
import torch
print(f'  PyTorch:  {torch.__version__}')
print(f'  CUDA:     {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'  CUDA Ver: {torch.version.cuda}')
    print(f'  GPU:      {torch.cuda.get_device_name(0)}')
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'  VRAM:     {vram:.1f} GB')
    print()
    print('  >> GPU mode ready / GPU 模式就绪!')
else:
    print()
    print('  >> CPU mode (no GPU acceleration / 无 GPU 加速)')
"@

# ---- Launch ----
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║     Setup Complete / 安装完成!             ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Starting app / 启动程序 ..." -ForegroundColor Cyan
Write-Host "  Browser / 浏览器: http://127.0.0.1:7860" -ForegroundColor White
Write-Host "  Ctrl+C to stop / 按 Ctrl+C 停止" -ForegroundColor Gray
Write-Host ""

& $venvPython main.py

Write-Host ""
Show-Info "App stopped / 程序已退出"
Read-Host "  Press Enter / 按回车退出"
