# Pauli semiweb diagrams

`main.tex` includes the discussion and Appendices I and J. `semiwebs/pauli_semiwebs.tex`
compiles the separate collection of 354 basis diagrams, and `detector_webs/detector_webs.tex`
the 127 declared-detector webs of the whole circuits.

From this directory:

```sh
latexmk -pdf main.tex
latexmk -pdf semiwebs/pauli_semiwebs.tex
latexmk -pdf detector_webs/detector_webs.tex
```

The diagram colours denote Pauli operators and phase defects. The text is black.
`semiwebs/index.tsv` lists the page numbers and basis elements. Each TikZ file
records the affected nodes and phase shifts in comments.
