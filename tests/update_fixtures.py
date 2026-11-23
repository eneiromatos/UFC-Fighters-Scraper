"""Re-download the UFC.com pages used by the tests, keeping only the parts the
scraper reads (so the fixtures stay small and readable).

    python tests/update_fixtures.py

Fighters' stats change over time, so after updating, some expected values in
test_fighters_stats.py may need updating too. A test that fails because a
field is suddenly missing means UFC changed its markup.
"""
import sys
import urllib.request
from pathlib import Path

from lxml import etree, html

FIXTURES = Path(__file__).parent / "fixtures"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

PAGES = {
    "jon-jones.html": "https://www.ufc.com/athlete/jon-jones",
    "mansur-abdul-malik.html": "https://www.ufc.com/athlete/mansur-abdul-malik",
    "athletes-all.html": "https://www.ufc.com/athletes/all",
}

# The page sections the spider reads.
KEEP = [
    ".hero-profile__info",
    ".stats-record-wrap",
    ".c-bio__info-details",
    ".c-listing-athlete-flipcard",
    "ul.pager",
]

# Noise inside those sections: chart drawings, tooltips, scripts.
DROP = "script, style, .tooltip, svg path, svg circle, svg line, img"


def remove(node):
    """Remove a node but keep any text that follows it."""
    parent = node.getparent()
    if node.tail and node.tail.strip():
        prev = node.getprevious()
        if prev is not None:
            prev.tail = (prev.tail or "") + node.tail
        else:
            parent.text = (parent.text or "") + node.tail
    parent.remove(node)


def trim(page_html):
    doc = html.fromstring(page_html)
    body = etree.Element("body")
    for css in KEEP:
        for node in doc.cssselect(css):
            body.append(node)
    for node in body.cssselect(DROP):
        remove(node)
    for el in body.iter():
        if el.text is not None and not el.text.strip():
            el.text = None
        if el.tail is not None and not el.tail.strip():
            el.tail = None
    # remove now-empty <g> groups left behind in the SVGs
    for g in reversed(list(body.iter("{*}g", "g"))):
        if len(g) == 0 and not (g.text or "").strip():
            remove(g)
    root = etree.Element("html")
    root.append(body)
    etree.indent(root, space="  ")
    return "<!DOCTYPE html>\n" + html.tostring(root, encoding="unicode") + "\n"


def main():
    for name, url in PAGES.items():
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            page = response.read().decode("utf-8")
        (FIXTURES / name).write_text(trim(page), encoding="utf-8")
        print(f"updated {name}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--trim-existing":
        # Trim the fixtures already on disk without downloading.
        for name in PAGES:
            path = FIXTURES / name
            path.write_text(trim(path.read_text(encoding="utf-8")), encoding="utf-8")
            print(f"trimmed {name}")
    else:
        main()
