# python and packages

## PyTorch will not install ("No matching distribution found for torch==2.2.2")
**Why:** Python 3.13 (or 3.12 on some setups). The last PyTorch build for Intel Macs is 2.2.2, which
supports Python up to 3.12; the project is pinned to Python 3.11.9 (`.python-version`).
**Fix:** install Python 3.11.9 (python.org installer or `pyenv install 3.11.9`), then
`python3.11 -m venv .venv`. `python setup.py` stops at step 0 if the interpreter is wrong.

## "A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x"
**Why:** a NumPy 2 release was installed (for example by `pip install` of another package without pins).
**Fix:** `pip install -r requirements.txt` again; it pins `numpy==1.26.4`. Never install packages one by one.

## PyMuPDF tries to compile from source and fails
**Why:** no prebuilt wheel for the interpreter (usually the wrong Python version).
**Fix:** use Python 3.11.9; `PyMuPDF==1.24.10` and `PyMuPDFb==1.24.10` have wheels for it on macOS,
Windows and Linux.

## the wrong Python runs even inside the virtual environment
**Why:** Anaconda's `base` environment activates automatically and comes first on the path; the prompt
shows `(.venv) (base)`.
**Fix:** `conda deactivate` before activating `.venv`, or permanently `conda config --set auto_activate_base false`.
Check with `python --version` (must print 3.11.9) and `which python` (must be inside `.venv`).

## Windows: activating the environment
`.venv\Scripts\activate` (PowerShell may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once).
Use `py -3.11 -m venv .venv` to pick Python 3.11. Windows has not been tested end to end (handover memo).
