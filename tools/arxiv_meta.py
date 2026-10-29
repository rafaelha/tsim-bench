"""Print title, authors and year of arXiv papers from the arXiv API.

Usage: python tools/arxiv_meta.py 2409.17595 [...]
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET

NS = {"a": "http://www.w3.org/2005/Atom"}
ids = ",".join(sys.argv[1:])
with urllib.request.urlopen(f"http://export.arxiv.org/api/query?id_list={ids}&max_results=100") as r:
    root = ET.fromstring(r.read())
for entry in root.findall("a:entry", NS):
    arxiv_id = entry.find("a:id", NS).text.rsplit("/", 1)[-1]
    title = " ".join(entry.find("a:title", NS).text.split())
    authors = [a.find("a:name", NS).text for a in entry.findall("a:author", NS)]
    year = entry.find("a:published", NS).text[:4]
    print(f"{arxiv_id} | {year} | {title} | {', '.join(authors)}")
