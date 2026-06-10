"""
ingest.py — Milestone 3: Document Ingestion & Chunking
-------------------------------------------------------
Loads all 10 .txt course-review files from documents/, cleans whitespace
artifacts, splits on double newlines first (to keep individual reviews
intact), then applies a 500-character sliding window with a 50-character
overlap. Returns a list of dicts with "text" and "source" keys.
Run directly to verify output:
    python ingest.py
"""
import os
import random
# ── Configuration ────────────────────────────────────────────────────────────
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHUNK_SIZE = 500      # characters
CHUNK_OVERLAP = 50    # characters
MIN_CHUNK_LENGTH = 50 # discard anything shorter than this
# ── Helpers ──────────────────────────────────────────────────────────────────
def load_documents(docs_dir: str) -> list[dict]:
    """
    Load every .txt file in docs_dir.
    Returns a list of {"text": <raw text>, "source": <filename>} dicts.
    """
    documents = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, encoding="utf-8", errors="replace") as f:
            raw = f.read()
        documents.append({"text": raw, "source": filename})
    return documents
def clean_text(text: str) -> str:
    """
    Normalize line endings, strip leading/trailing whitespace, and
    collapse runs of 3+ blank lines down to exactly two newlines so
    that double-newline splitting stays consistent.
    """
    # Normalize Windows CRLF → LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ consecutive newlines → exactly 2
    import re
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
def split_into_paragraphs(text: str) -> list[str]:
    """
    Split on double newlines to get natural paragraph / review boundaries.
    Returns only non-empty, non-whitespace-only paragraphs.
    """
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]
def sliding_window_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Apply a character-level sliding window to a single text block.
    Produces chunks of up to `chunk_size` characters, stepping by
    (chunk_size - overlap) on each iteration.
    """
    step = chunk_size - overlap
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start += step
    return [c for c in chunks if c]
def chunk_document(doc: dict, chunk_size: int, overlap: int) -> list[dict]:
    """
    Full chunking pipeline for a single document:
      1. Clean text
      2. Split on double newlines (keep reviews intact where possible)
      3. For any paragraph that fits within chunk_size, keep it whole.
         For paragraphs longer than chunk_size, apply the sliding window.
      4. Discard chunks shorter than MIN_CHUNK_LENGTH.
    Returns a list of {"text": <chunk>, "source": <filename>} dicts.
    """
    cleaned = clean_text(doc["text"])
    paragraphs = split_into_paragraphs(cleaned)
    chunks = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            # Paragraph fits — keep it as one chunk
            if len(para) >= MIN_CHUNK_LENGTH:
                chunks.append({"text": para, "source": doc["source"]})
        else:
            # Paragraph is too long — apply sliding window
            for window in sliding_window_chunks(para, chunk_size, overlap):
                if len(window) >= MIN_CHUNK_LENGTH:
                    chunks.append({"text": window, "source": doc["source"]})
    return chunks
def load_and_chunk_all(docs_dir: str = DOCUMENTS_DIR) -> list[dict]:
    """
    Public entry point. Loads every .txt file and returns the full
    list of chunk dicts with "text" and "source" keys.
    """
    documents = load_documents(docs_dir)
    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP))
    return all_chunks
# ── Verification (runs when executed directly) ────────────────────────────────
if __name__ == "__main__":
    chunks = load_and_chunk_all()
    print(f"\n{'='*60}")
    print(f"  Total chunks produced: {len(chunks)}")
    print(f"{'='*60}\n")
    # Verification criteria from planning.md:
    # (1) readable as standalone opinion
    # (2) correct source filename in metadata
    # (3) no leftover whitespace artifacts or empty strings
    # (4) between 50 and 500 characters long
    print("── 5 random sample chunks ──────────────────────────────────\n")
    sample = random.sample(chunks, min(5, len(chunks)))
    for i, chunk in enumerate(sample, 1):
        length = len(chunk["text"])
        print(f"[{i}] source: {chunk['source']}  |  length: {length} chars")
        print(f"    {repr(chunk['text'][:120])}{'...' if length > 120 else ''}")
        print()
    # Automated checks
    print("── Automated verification ───────────────────────────────────\n")
    failures = []
    for idx, chunk in enumerate(chunks):
        text = chunk["text"]
        src = chunk["source"]
        if not text or not text.strip():
            failures.append(f"Chunk {idx} ({src}): empty or whitespace-only")
        if len(text) < MIN_CHUNK_LENGTH:
            failures.append(f"Chunk {idx} ({src}): too short ({len(text)} chars)")
        if len(text) > CHUNK_SIZE:
            failures.append(f"Chunk {idx} ({src}): too long ({len(text)} chars)")
        if not src.endswith(".txt"):
            failures.append(f"Chunk {idx}: source filename missing .txt extension")
        if text != text.strip():
            failures.append(f"Chunk {idx} ({src}): leading/trailing whitespace present")
    if failures:
        print(f"FAILED — {len(failures)} issue(s) found:")
        for f in failures:
            print(f"  ✗ {f}")
    else:
        print(f"ALL CHECKS PASSED ✓")
        print(f"  • {len(chunks)} chunks, all between {MIN_CHUNK_LENGTH}–{CHUNK_SIZE} chars")
        print(f"  • No empty or whitespace-only chunks")
        print(f"  • All chunks carry a .txt source filename")
