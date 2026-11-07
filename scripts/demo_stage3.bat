@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."

echo ===== Test repository: normal cases =====
for %%n in (simple chain multi_letter) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml
    echo exit code: !errorlevel!
)

echo ===== Test repository: cyclic dependencies =====
for %%n in (cyclic self_loop) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml
    echo exit code: !errorlevel!
)

echo ===== Test repository: filter =====
for %%n in (filter_b filter_d filter_case) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml
    echo exit code: !errorlevel!
)

echo ===== Test repository: dependency missing from the file =====
python -m src.main --config configs\test_undefined.yaml
echo exit code: !errorlevel!

echo ===== Test repository: errors =====
for %%n in (missing_root filter_root broken_syntax broken_name broken_duplicate) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml
    echo exit code: !errorlevel!
)

echo ===== Real repository (PyPI), needs internet =====
for %%n in (requests requests_filter flask flask_filter) do (
    echo --- configs\%%n.yaml
    python -m src.main --config configs\%%n.yaml
    echo exit code: !errorlevel!
)

echo ===== Real repository: errors =====
for %%n in (missing_package bad_host) do (
    echo --- configs\%%n.yaml
    python -m src.main --config configs\%%n.yaml
    echo exit code: !errorlevel!
)

echo ===== Invalid configuration files =====
for %%f in (configs\errors\*.yaml) do (
    echo --- %%f
    python -m src.main --config %%f
    echo exit code: !errorlevel!
)
