# Literature scout brief (shared by 20 parallel scouts)

GOAL: find papers (arXiv preferred) whose authors released quantum-error-correction /
fault-tolerance circuits in Stim format (.stim files, or code that generates `stim.Circuit`
objects) that either

(a) already contain non-Clifford gates (T, T_DAG, CCZ, CCX, CS, small-angle rotations), or
(b) are Clifford proxies that can easily be turned into real non-Clifford circuits, e.g.
    Gidney-style magic state cultivation (T gates simulated with S/S_DAG, or the |i>/|Y>
    proxy), injection circuits, distillation factories where T is replaced by a Clifford
    stand-in, coherent-rotation noise circuits, etc.

These circuits will be simulated with near-Clifford samplers (QuEra Tsim, Clifft), which accept
Stim syntax plus T, T_DAG, R_Z/R_X/R_Y, CCZ, CCX, etc.

Stay within YOUR SEARCH ANGLE (given in your task message) as much as possible; other
scouts cover other angles. Use web search, arXiv listings/abstracts, Google Scholar, GitHub,
Zenodo, figshare, and the papers' "Code availability"/"Data availability" sections. For each
candidate, try hard to find WHERE the circuits live (GitHub repo URL, Zenodo DOI,
supplementary files, arXiv ancillary files at https://arxiv.org/src/<id>/anc) and whether
they are actual .stim files or generator code. Verify links exist when you can. Aim for
roughly 5-15 solid candidates; quality over quantity. Excluding papers with no released
circuits/code is fine, but list "maybe" candidates with low confidence if circuits might
be reconstructable from released code.

DO NOT download paper sources or large datasets, do not modify any file other than your single
output file, and do not install packages.

OUTPUT: write a JSON file to `/home/rafaelha/quera/tsim-active-width/_search/<YOUR_ID>.json`
containing a list of objects with fields:

- `arxiv_id` (e.g. "2409.17595", or null)
- `title`
- `authors` (short, e.g. "Gidney, Shutty, Jones")
- `year`
- `circuit_location` (list of URLs: GitHub / Zenodo / anc files)
- `format` ("stim files" | "generator code" | "both" | "unknown")
- `non_clifford_status` ("native T/CCZ in files" | "Clifford proxy, convertible" | "unclear")
- `conversion_notes` (how to get real T/CCZ/CS gates: which gates/lines to replace)
- `confidence` ("high" | "medium" | "low")
- `notes`

Then reply with a short summary, one line per paper: arxiv id, title, location. Keep the reply concise.
