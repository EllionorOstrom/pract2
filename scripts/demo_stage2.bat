@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."

echo ===== Direct dependencies from PyPI =====
for %%f in (configs\requests.yaml configs\flask.yaml) do (
    echo --- %%f
    python -m src.main --config %%f
    echo exit code: !errorlevel!
)

echo ===== Package does not exist =====
python -m src.main --config configs\missing_package.yaml
echo exit code: !errorlevel!

echo ===== Repository is unreachable =====
python -m src.main --config configs\bad_host.yaml
echo exit code: !errorlevel!

echo ===== Invalid configuration =====
python -m src.main --config configs\errors\bad_url.yaml
echo exit code: !errorlevel!
