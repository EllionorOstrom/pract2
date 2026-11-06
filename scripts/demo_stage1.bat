@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."

echo ===== Correct configurations =====
for %%f in (config.yaml configs\remote.yaml configs\test.yaml) do (
    echo --- %%f
    python -m src.main --config %%f
    echo exit code: !errorlevel!
)

echo ===== Configuration file does not exist =====
python -m src.main --config configs\no_such_file.yaml
echo exit code: !errorlevel!

echo ===== Invalid configurations =====
for %%f in (configs\errors\*.yaml) do (
    echo --- %%f
    python -m src.main --config %%f
    echo exit code: !errorlevel!
)
