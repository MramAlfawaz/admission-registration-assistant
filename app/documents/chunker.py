"""Split extracted documents into retrievable chunks with metadata."""
import re

META_FIELDS = ("source_id", "title", "document_type", "authority_level", "version",
               "effective_from", "effective_to", "language", "status")
ARTICLE = re.compile(r"(?:المادة|مادة)\s*\(?\s*(\d+)\s*\)?")
TARGET_WORDS = 160
OVERLAP_MAX_WORDS = 60


def _meta(source):
    """Copy the metadata fields every chunk must carry."""
    return {k: source.get(k) for k in META_FIELDS}


def _is_heading(block):
    """Guess whether a block is a short section heading."""
    words = block.split()
    return 0 < len(words) <= 7 and not block.endswith((".", "،", ":", "؛")) \
        and not re.search(r"\d", block)


def _blocks(pages):
    """Yield (page_number, block_text) for each paragraph block."""
    for number, page in enumerate(pages, 1):
        for raw in re.split(r"\n\s*\n", page):
            text = " ".join(line.strip() for line in raw.splitlines() if line.strip())
            if text:
                yield number, text


def chunk_text(pages, source):
    """Pack paragraph blocks into chunks of about TARGET_WORDS words.

    Args:
        pages: list of page texts.
        source: the source metadata dictionary.

    Returns:
        A list of chunk dictionaries.
    """
    chunks, current, heading = [], [], None

    def flush():
        if not current:
            return
        text = "\n".join(b for _, b, _ in current)
        article = ARTICLE.search(text)
        chunks.append({
            **_meta(source),
            "chunk_id": f"{source['source_id']}#{len(chunks) + 1:03d}",
            "page": current[0][0],
            "page_end": current[-1][0],
            "section": current[0][2],
            "article": article.group(1) if article else None,
            "text": text,
        })

    for page, block in _blocks(pages):
        if _is_heading(block):
            heading = block
        current.append((page, block, heading))
        if sum(len(b.split()) for _, b, _ in current) >= TARGET_WORDS:
            flush()
            last = current[-1]
            current = [last] if len(last[1].split()) <= OVERLAP_MAX_WORDS else []
    flush()
    return chunks


def chunk_faq(pages, source):
    """Make one chunk per question and its answer.

    Args:
        pages: list of page texts (an FAQ page is a single page).
        source: the source metadata dictionary.

    Returns:
        A list of chunk dictionaries.
    """
    chunks, question, answer = [], None, []

    def flush():
        if question and answer:
            chunks.append({
                **_meta(source),
                "chunk_id": f"{source['source_id']}#{len(chunks) + 1:03d}",
                "page": 1, "page_end": 1, "section": question, "article": None,
                "text": question + "\n" + " ".join(answer),
            })

    for line in "\n".join(pages).splitlines():
        line = line.strip()
        if not line:
            continue
        if line.endswith("؟") or line.endswith("?"):
            flush()
            question, answer = line, []
        elif question:
            answer.append(line)
    flush()
    return chunks


def chunk_calendar(events, source):
    """Make one chunk per calendar event.

    Args:
        events: structured events from the calendar parser.
        source: the source metadata dictionary.

    Returns:
        A list of chunk dictionaries.
    """
    chunks = []
    for e in events:
        g = e["date_start"] if e["date_start"] == e["date_end"] else f"{e['date_start']} إلى {e['date_end']}"
        h = e["hijri_start"] if e["hijri_start"] == e["hijri_end"] else f"{e['hijri_start']} إلى {e['hijri_end']}"
        chunks.append({
            **_meta(source),
            "chunk_id": f"{source['source_id']}#{e['row']:03d}",
            "page": 1, "page_end": 1, "section": e["section"], "article": None,
            "text": f"{e['event']}: {e['day']} {g}م ({h}هـ)",
            "event_code": e["code"], "term_id": e["term_id"],
        })
    return chunks
