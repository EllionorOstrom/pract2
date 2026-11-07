@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist out mkdir out

echo ===== PlantUML: test repository =====
for %%n in (simple cyclic multi_letter) do (
    echo --- configs\test_%%n.yaml
    python -m src.main --config configs\test_%%n.yaml --mode plantuml --output out\test_%%n.puml
    echo exit code: !errorlevel!
)

echo ===== PlantUML: three real packages (internet) =====
for %%n in (requests flask jinja2) do (
    echo --- configs\%%n.yaml
    python -m src.main --config configs\%%n.yaml --mode plantuml --output out\%%n.puml
    echo exit code: !errorlevel!
)

echo ===== PlantUML: errors =====
python -m src.main --config configs\test_missing_root.yaml --mode plantuml
echo exit code: !errorlevel!
python -m src.main --config configs\test_simple.yaml --mode plantuml --output no_such_dir\g.puml
echo exit code: !errorlevel!

echo ===== Comparison with pipdeptree (temporary virtualenv, internet) =====
for %%n in (requests flask jinja2) do (
    echo --- configs\%%n.yaml
    python -m src.compare --config configs\%%n.yaml --what graph
    echo exit code: !errorlevel!
)
