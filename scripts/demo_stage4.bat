@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."

echo ===== Load order: test repository =====
for %%n in (simple chain multi_letter filter_b) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml --mode order
    echo exit code: !errorlevel!
)

echo ===== Load order: cyclic dependencies =====
for %%n in (cyclic self_loop) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml --mode order
    echo exit code: !errorlevel!
)

echo ===== Load order: errors =====
for %%n in (missing_root filter_root broken_syntax) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml --mode order
    echo exit code: !errorlevel!
)

echo ===== Load order: real packages (internet) =====
for %%n in (requests flask) do (
    echo --- configs\%%n.yaml
    python -m src.main --config configs\%%n.yaml --mode order
    echo exit code: !errorlevel!
)

echo ===== Comparison with pip (creates a temporary virtualenv, internet) =====
for %%n in (requests flask) do (
    echo --- configs\%%n.yaml
    python -m src.compare --config configs\%%n.yaml
    echo exit code: !errorlevel!
)
