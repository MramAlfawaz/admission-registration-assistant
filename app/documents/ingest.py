"""Build chunks for one source from its raw file."""
from pathlib import Path

from app.documents.calendar_parser import parse_calendar
from app.documents.chunker import chunk_calendar, chunk_faq, chunk_text
from app.documents.loader import extract_pages


def build_chunks(source, raw_dir):
    """Extract and chunk one source according to its document type.

    Args:
        source: the source metadata dictionary.
        raw_dir: folder holding the downloaded files.

    Returns:
        A list of chunk dictionaries.
    """
    pages = extract_pages(Path(raw_dir) / source["filename"])
    if source["document_type"] == "calendar":
        events = parse_calendar("\n".join(pages), source["source_id"], source["version"])
        return chunk_calendar(events, source)
    if source["document_type"] == "faq":
        return chunk_faq(pages, source)
    return chunk_text(pages, source)
