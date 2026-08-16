"""Deterministic cleaning and bounded chunking for the TRACE pipeline.

Training and inference should import the same functions so that preprocessing cannot
silently diverge between the two paths.

The pipeline:
  1. strip_boiler  — drop corpus-frequent lines (nav/footer/"From: Department of ..."),
                     using a frozen set derived from the training corpus.
  2. clean_markup  — static regexes: WordPress/Visual-Composer CSS shortcodes, [vc_/wpb_]
                     brackets, obfuscated [email protected], www-tokens, 28+char css junk,
                     FFT-Datalab / blog-subscribe footers.
  3. chunk_doc     — sentence-boundary-aware ~100-word chunks, cap 40/doc.

Deliberately absent: lowercasing, stemming and entity removal. Those choices must be made
explicitly by the caller rather than appearing as train/serve skew.

Regenerate a frozen boilerplate set from a caller-supplied CSV:
    python -m trace_evidence.preprocessing --freeze-from INPUT.csv --output boilerplate.txt
Inspect cleaning on a junk sample:
    python -m trace_evidence.preprocessing --selftest
"""
from __future__ import annotations

import re
from pathlib import Path

BOILER_THRESHOLD = 0.02
TARGET_WORDS = 100
MAX_CHUNKS_PER_DOC = 40
NL = chr(10)

# --- static markup regexes -------------------------------------------------- #
_MARKUP = re.compile(r"\b\w*(?:vcrow|vccolumn|cssvc|singleimage|imgsize|addcaption|alignmentcenter|wpb_)\w*\b", re.I)
_LONGTOK = re.compile(r"\b\w{28,}\b")
_SHORTCODE = re.compile(r"\[/?(?:vc_|wpb_|et_pb_)[^\]]*\]", re.I)
_EMAILBR = re.compile(r"\[email\s*protected\]", re.I)
_URL = re.compile(r"\bwww\w+\b", re.I)
_FOOTER = re.compile(
    r"want to stay up-?to-?date with the latest research from fft education datalab.*?half-?termly newsletter\.?"
    r"|(?:get our updates via email\s*)?enter your email address to subscribe to this blog and receive "
    r"notifications of new posts by email\.?(?:\s*email address\s*subscribe)?",
    re.I | re.S)

# Safe public fallback. Production callers should supply their frozen set explicitly.
_DEFAULT_BOILER = {"From: Department of Education and Youth"}


def clean_markup(t: str) -> str:
    """Apply the static, data-independent markup and footer rules."""
    t = _FOOTER.sub(" ", t)
    t = _SHORTCODE.sub(" ", t)
    t = _EMAILBR.sub(" ", t)
    t = _URL.sub(" ", t)
    t = _MARKUP.sub(" ", t)
    t = _LONGTOK.sub(" ", t)
    t = re.sub(r"\b(?:emailprotected|cdata)\b", " ", t, flags=re.I)
    return re.sub(r"[ \t]+", " ", t)


def load_boilerplate(path: Path | None = None) -> set[str]:
    """Load a caller-supplied frozen boilerplate set, or use the public fallback."""
    if path is not None and path.exists():
        lines = {ln.rstrip(NL) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}
        return lines or set(_DEFAULT_BOILER)
    return set(_DEFAULT_BOILER)


def strip_boiler(t: str, boiler: set[str]) -> str:
    """Drop whole lines that exactly match a frozen boilerplate line."""
    return NL.join(l for l in t.split(NL) if l.strip() not in boiler)


def clean_doc(t: str, boiler: set[str] | None = None) -> str:
    """Run boilerplate removal followed by static markup cleaning."""
    if boiler is None:
        boiler = load_boilerplate()
    return clean_markup(strip_boiler(str(t), boiler))


# --- bounded chunking ------------------------------------------------------- #
def sent_split(t: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", t.strip()) if s]


def chunk_doc(t: str, target: int = TARGET_WORDS, cap: int | None = MAX_CHUNKS_PER_DOC) -> list[str]:
    out, cur, cw = [], [], 0
    for s in sent_split(t):
        w = len(s.split())
        if cw + w > target and cur:
            out.append(" ".join(cur)); cur, cw = [], 0
        cur.append(s); cw += w
    if cur:
        out.append(" ".join(cur))
    out = out or [t]
    return out[:cap] if cap else out


def prepare(text: str, boiler: set[str] | None = None) -> list[str]:
    """Raw doc text -> clean -> chunk -> list of chunk strings (the unit inference scores)."""
    return chunk_doc(clean_doc(text, boiler))


# --- freeze the boilerplate set from the training corpus -------------------- #
def freeze_boilerplate(
    corpus_csv: Path,
    output: Path | None = None,
    threshold: float = BOILER_THRESHOLD,
) -> set[str]:
    """Derive repeated boilerplate lines from a caller-supplied corpus."""
    import pandas as pd
    from collections import Counter
    df = pd.read_csv(corpus_csv)
    texts = df["text"].fillna("").astype(str)
    lines: Counter = Counter()
    for t in texts:
        for ln in set(l.strip() for l in t.split(NL) if 15 < len(l.strip()) < 160):
            lines[ln] += 1
    boiler = {l for l, n in lines.items() if n > len(df) * threshold}
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(NL.join(sorted(boiler)) + NL, encoding="utf-8")
        print(f"froze {len(boiler)} boilerplate line(s) -> {output}")
    for l in sorted(boiler):
        print(f"  · {l[:90]}")
    return boiler


def _selftest() -> None:
    boiler = load_boilerplate()
    print(f"frozen boilerplate lines loaded: {len(boiler)}")
    sample = (
        "From: Department of Education and Youth\n"
        "[vc_row][vc_column] The Minister announced new funding for schools. "
        "Contact us at [email protected] or visit wwweducationgovuk for details. "
        "cssvc_custom_12345 alignmentcenter This is a real sentence about Ofsted inspections. "
        "Enter your email address to subscribe to this blog and receive notifications of new posts by email."
    )
    cleaned = clean_doc(sample, boiler)
    print("\n--- RAW ---\n" + sample)
    print("\n--- CLEANED ---\n" + cleaned)
    print("\n--- CHUNKS ---")
    for i, c in enumerate(chunk_doc(cleaned)):
        print(f"  [{i}] {c}")


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--freeze-from", type=Path, help="CSV with a text column")
    p.add_argument("--output", type=Path, help="where to write the frozen line set")
    p.add_argument("--selftest", action="store_true", help="run clean+chunk on a junk sample")
    a = p.parse_args()
    if a.freeze_from:
        if a.output is None:
            p.error("--freeze-from requires --output")
        freeze_boilerplate(a.freeze_from, a.output)
    if a.selftest or not a.freeze_from:
        _selftest()


if __name__ == "__main__":
    main()
