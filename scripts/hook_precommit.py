#!/usr/bin/env python3
"""
Hook PreToolUse para Claude Code.
Valida los CSVs automáticamente antes de ejecutar 'git commit'.
Recibe el tool call como JSON en stdin.
"""
import json, sys, os, subprocess

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # Si no llegan datos, dejar pasar sin bloquear

tool_name  = data.get("tool_name", "")
tool_input = data.get("tool_input", {})
command    = tool_input.get("command", "")

# Solo actuar cuando Claude va a hacer un git commit
if "git commit" not in command:
    sys.exit(0)

# Ruta al script de validación
script_dir  = os.path.dirname(os.path.abspath(__file__))
validar_csv = os.path.join(script_dir, "validar_csv.py")

print("🔍 Pre-commit: validando CSVs...")

result = subprocess.run(
    [sys.executable, validar_csv],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

if result.stdout:
    print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

if result.returncode != 0:
    print("\n🚫 Commit bloqueado: hay errores en los CSVs. Corrígelos primero.")
    sys.exit(1)

sys.exit(0)
