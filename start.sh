#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
command -v python3 >/dev/null || { echo "python3 topilmadi. O'rnating: sudo apt install python3 python3-venv"; exit 1; }
[ -d .venv ] || { echo "Birinchi marta: tayyorlanmoqda..."; python3 -m venv .venv || exit 1; }
. .venv/bin/activate
pip install -q -r requirements.txt
while true; do
  python bot.py
  echo "Bot to'xtadi. 5 soniyadan keyin qayta ishga tushadi (to'xtatish: Ctrl+C)."
  sleep 5
done
