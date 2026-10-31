#!/usr/bin/env bash
# The automated part of the definition of done (Development Standards, Part 5): a fresh clone
# installs, bootstraps, passes the tests and reproduces the committed held-out results from the
# committed model cache. It does not replace a test by someone outside the team.
#
#   bash scripts/clean_install_check.sh                 # clones from GitHub
#   bash scripts/clean_install_check.sh /path/to/repo   # or from a local clone
#
# Needs: git, Python 3.11, and Ollama running with qwen2.5:3b (ollama pull qwen2.5:3b).
# Windows: run it from Git Bash; set PYTHON=py if python3.11 is not on the path.
set -euo pipefail

REPO="${1:-https://github.com/MramAlfawaz/admission-registration-assistant.git}"
PYTHON="${PYTHON:-python3.11}"
REFERENCE="${REFERENCE:-holdout_v4}"
WORK="$(mktemp -d)"
START=$(date +%s)
stage() { echo "== [$(( $(date +%s) - START ))s] $*"; }

stage "cloning $REPO into $WORK"
git clone --quiet --depth 1 "$REPO" "$WORK/repo"
cd "$WORK/repo"

stage "creating the virtual environment with $PYTHON"
"$PYTHON" -m venv .venv
if [ -f .venv/bin/activate ]; then source .venv/bin/activate; else source .venv/Scripts/activate; fi

stage "installing the pinned packages"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

stage "bootstrap (documents, chunks, embedding model, model check)"
python setup.py

stage "tests"
python -m pytest -q

stage "reproducing $REFERENCE from the committed cache"
python cli.py evaluate-e2e --set holdout --out clean_check --no-repeat
python cli.py compare-runs "$REFERENCE" clean_check

stage "clean install check passed in $(( ($(date +%s) - START) / 60 )) min (folder: $WORK)"
