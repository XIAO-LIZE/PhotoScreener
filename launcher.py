"""Photo Screener - One-click installer & launcher"""
import subprocess
import sys
import shutil
import urllib.request
from pathlib import Path

# ── Find project root ──────────────────────────────────────
if getattr(sys, "frozen", False):
    project_dir = Path(sys.executable).resolve().parent
else:
    project_dir = Path(__file__).resolve().parent

# Search upward for project root (contains main.py)
for _ in range(4):
    if (project_dir / "main.py").exists():
        break
    project_dir = project_dir.parent

VENV = project_dir / ".venv"
PYTHON = VENV / "Scripts" / "python.exe"
REQUIREMENTS = project_dir / "requirements.txt"
MAIN = project_dir / "main.py"

# Pip mirrors
PYPI_URL = "https://pypi.org/simple"
TSINGHUA_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"


def detect_pip_index() -> str:
    """Auto-detect best pip mirror by testing connectivity."""
    try:
        req = urllib.request.Request(PYPI_URL, method="HEAD")
        urllib.request.urlopen(req, timeout=2)
        print("  [Detect] pypi.org reachable → using default index")
        return PYPI_URL
    except Exception:
        print("  [Detect] pypi.org unreachable → using Tsinghua mirror")
        print("  检测到 PyPI 不可达，自动切换清华镜像")
        return TSINGHUA_URL


def step(msg: str):
    print(f"\n  >>> {msg}")


def ok(msg: str):
    print(f"  [OK] {msg}")


def fail(msg: str):
    print(f"  [ERROR] {msg}")
    print("")
    input("  Press Enter to exit / 按回车退出...")
    sys.exit(1)


def run(cmd: list, desc: str = "", cwd=None):
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or project_dir)
    if result.returncode != 0:
        fail(f"{desc} failed" if desc else "Command failed")
    return result


def ensure_venv():
    """Create .venv if missing, install dependencies."""
    if VENV.exists() and PYTHON.exists():
        return  # venv already exists

    step("Creating virtual environment...")
    # Find system Python
    system_python = shutil.which("python") or shutil.which("python3")
    if not system_python:
        fail("Python not found. Please install Python 3.10+ first.\n"
             "   Python 未找到，请先安装 Python 3.10+。\n"
             "   https://www.python.org/downloads/")

    run([system_python, "-m", "venv", str(VENV), "--clear"],
        "Create venv")

    step("Installing dependencies...")
    pip_index = detect_pip_index()
    print("  This may take a few minutes / 这可能需要几分钟...")
    run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip",
         "-i", pip_index], "Upgrade pip")
    run([str(PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS),
         "-i", pip_index], "Install requirements")
    ok("Dependencies installed")


def launch():
    """Start main.py with the venv Python."""
    step("Starting Photo Screener...")
    print("  Browser will open at: http://127.0.0.1:7860")
    print("  Ctrl+C to stop / 按 Ctrl+C 停止")
    print("=" * 50)
    result = subprocess.run([str(PYTHON), str(MAIN)], cwd=project_dir)
    sys.exit(result.returncode)


# ── Main ───────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  Photo Screener / 照片筛选器")
    print("=" * 50)

    if not MAIN.exists():
        fail(f"main.py not found at: {MAIN}\n"
             "  Please keep this exe alongside the project files.\n"
             "  请将此 exe 与项目文件放在一起。")

    ensure_venv()
    launch()


if __name__ == "__main__":
    main()
