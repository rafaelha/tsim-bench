#!/usr/bin/env bash
# Download and unpack the arXiv source of a paper into <dir>/tex, then list code/data links in it.
# Usage: tools/fetch_arxiv.sh <arxiv-id> <dir>
set -euo pipefail
id=$1; dir=$2
mkdir -p "$dir/tex"
tmp=$(mktemp)
curl -sSL -A "Mozilla/5.0 tsim-active-width survey" "https://arxiv.org/src/$id" -o "$tmp"
kind=$(file -b "$tmp")
case "$kind" in
  *gzip*) if tar -tzf "$tmp" >/dev/null 2>&1; then tar -xzf "$tmp" -C "$dir/tex"; else gunzip -c "$tmp" > "$dir/tex/main.tex"; fi ;;
  *tar*) tar -xf "$tmp" -C "$dir/tex" ;;
  *PDF*) cp "$tmp" "$dir/tex/paper.pdf"; echo "WARNING: arXiv only provides a PDF" ;;
  *) cp "$tmp" "$dir/tex/main.tex" ;;
esac
rm -f "$tmp"
echo "== files"; find "$dir/tex" -type f | head -40
echo "== links"
grep -rhoE "https?://[^ }{\\\"']*(github|zenodo|gitlab|figshare|doi.org/10.5281|codeocean|bitbucket|algassert|dryad)[^ }{\\\"']*" "$dir/tex" --include=*.tex --include=*.bbl --include=*.bib 2>/dev/null | sort -u | head -30
