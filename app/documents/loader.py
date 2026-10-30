"""Extract text from source files."""
from pathlib import Path

import fitz
from bs4 import BeautifulSoup

from app.documents.normalize import clean_text

HTML_BOILERPLATE = {"NAUSS", "الرئيسية", "محتوى الصفحة", "شارك"}


def fix_ligature_order(chars):
    """Restore logical order for letters split out of one ligature glyph.

    PyMuPDF expands a ligature glyph such as lam-alef into a letter that
    carries the glyph width and a zero-width letter placed at its right
    edge, and emits the zero-width letter first. This swaps such pairs.

    Args:
        chars: list of (char, x0, x1) tuples in extraction order.

    Returns:
        The characters joined into a string, with each pair repaired.
    """
    out = list(chars)
    i = 0
    while i < len(out) - 1:
        c, x0, x1 = out[i]
        n, nx0, nx1 = out[i + 1]
        is_zero_width_letter = c.isalpha() and abs(x1 - x0) < 0.01
        sits_on_next_edge = (nx1 - nx0) > 0.01 and abs(x0 - nx1) < 0.05
        if is_zero_width_letter and sits_on_next_edge:
            out[i], out[i + 1] = out[i + 1], out[i]
            i += 2
        else:
            i += 1
    return "".join(c for c, _, _ in out)


def _pdf_page_text(page):
    """Return one PDF page's text with ligature order repaired."""
    lines = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            chars = [(ch["c"], ch["bbox"][0], ch["bbox"][2])
                     for span in line["spans"] for ch in span["chars"]]
            lines.append(fix_ligature_order(chars))
        lines.append("")
    return "\n".join(lines)


def extract_pages(path):
    """Return the cleaned text of a PDF or HTML file, one string per page.

    Args:
        path: path to the file.

    Returns:
        A list of strings. An HTML file returns a single page.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as doc:
            return [clean_text(_pdf_page_text(page)) for page in doc]
    if suffix in (".html", ".htm"):
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        main = soup.find("main") or soup.body or soup
        text = clean_text(main.get_text("\n", strip=True))
        lines = [ln for ln in text.splitlines() if ln and ln not in HTML_BOILERPLATE]
        return ["\n".join(lines)]
    raise ValueError(f"unsupported file type: {suffix}")
