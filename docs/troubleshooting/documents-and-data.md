# documents and data

## `setup.py`: "documents not downloaded"
**Why:** nauss.edu.sa is down, slow, or a document moved.
**Fix:** open the URL from `data/sources.json` in a browser. If the file moved, update `url`; if it is
temporarily down, try later. You can also place the file in `data/raw/` with the `filename` from
`data/sources.json`; `fetch` skips files already present.

## `setup.py`: "chunks differ from the ones the results were measured on"
**Why:** a document at the same URL was replaced, so the text changed.
**Fix:** the application still works. To keep results reproducible, register the new file as a new version
(`add-source`, handover memo section 6) and re-run the evaluations; report both.

## every deadline question answers "no calendar in force"
**Why:** the question's date (`as_of`) is outside every registered calendar (the 1448 calendar is in
force from 2026-08-12 to 2027-08-21, `data/sources.json`).
**Fix:** add the new calendar with `add-source --type calendar`, then `build-calendar` and `ingest`.

## Arabic text in `peek` output reads backwards or with letters out of order
**Why:** PDF text extraction of right-to-left text. `app/documents/loader.py` repairs reversed words for
`PyMuPDF==1.24.10`; a different version orders glyphs differently.
**Fix:** reinstall the pinned version. 4 reversed words remain (known limitation).
