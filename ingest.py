"""
Document ingestion pipeline for the Healthcare RAG API.

Reads source documents from a directory, parses supported file types, splits
them into overlapping chunks with deterministic recursive-character splitting,
and produces ``(texts, ids, metadatas)`` ready for a vector store.

Design notes
------------
* Pure and free of heavy side effects (no embedding model, no network calls),
  which keeps the whole module fast and unit-testable.
* Chunk metadata mirrors the convention used in the course material
  (``docs/.../examples/01-deterministic-chunking.py``): ``chunk_index``,
  ``char_start``, ``char_end`` -- plus provenance fields (``doc_id``,
  ``filename``, ``doc_type``, ``total_chunks``, ``source``) that are
  forward-compatible with full provenance tracking (assessment P0-4).
* Every chunk satisfies the invariant ``text[char_start:char_end] == chunk_text``,
  so a retrieved chunk can always be located back in its source document.
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# File types the loader understands. PDF support is best-effort (see _load_pdf).
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".txt", ".md", ".pdf")

# Split on sentence terminators followed by whitespace, or on blank lines.
_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}")


@dataclass(frozen=True)
class Chunk:
    """A single indexable unit of text with provenance metadata."""

    id: str
    text: str
    metadata: dict


@dataclass(frozen=True)
class CorpusBuildResult:
    """Parallel arrays ready to hand to a vector store, plus a fingerprint."""

    texts: list[str]
    ids: list[str]
    metadatas: list[dict]
    fingerprint: str
    num_documents: int
    num_chunks: int


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def discover_documents(data_dir: str | Path) -> list[Path]:
    """Return supported document paths under ``data_dir``, sorted for determinism."""
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Corpus directory not found: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Corpus path is not a directory: {root}")
    paths = [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(paths)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def load_document(path: str | Path) -> str:
    """Extract plain text from a supported document.

    ``.txt`` / ``.md`` are read directly. ``.pdf`` uses ``pypdf`` if it is
    installed; if not, the PDF is skipped (returns ``""``) with a warning so the
    rest of the corpus still loads.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".txt", ".md"):
        return p.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        return _load_pdf(p)
    raise ValueError(f"Unsupported file type: {p.suffix or '<none>'} ({p})")


def _load_pdf(path: Path) -> str:
    try:
        import pypdf
    except ImportError:
        logger.warning("pypdf not installed; skipping PDF file %s", path)
        return ""
    try:
        reader = pypdf.PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception as exc:  # noqa: BLE001 - one bad PDF must not break ingestion
        logger.warning("Failed to parse PDF %s: %s", path, exc)
        return ""


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def _segment(text: str) -> list[tuple[str, int, int]]:
    """Split text into sentence/paragraph atoms as ``(text, start, end)`` tuples.

    Each atom is stripped of surrounding whitespace but its offsets point into
    the original string, so ``text[start:end] == atom_text``.
    """
    atoms: list[tuple[str, int, int]] = []

    def _emit(seg: str, base: int) -> None:
        if not seg.strip():
            return
        lead = len(seg) - len(seg.lstrip())
        core = seg.strip()
        start = base + lead
        atoms.append((core, start, start + len(core)))

    last = 0
    for m in _BOUNDARY_RE.finditer(text):
        _emit(text[last:m.start()], last)
        last = m.end()
    _emit(text[last:], last)
    return atoms


def _hard_split(
    atoms: list[tuple[str, int, int]], chunk_size: int, overlap: int
) -> list[tuple[str, int, int]]:
    """Break any atom longer than ``chunk_size`` into overlapping sub-atoms."""
    step = max(1, chunk_size - overlap)
    out: list[tuple[str, int, int]] = []
    for text, start, end in atoms:
        if len(text) <= chunk_size:
            out.append((text, start, end))
            continue
        i = 0
        while i < len(text):
            sub = text[i : i + chunk_size]
            out.append((sub, start + i, start + i + len(sub)))
            if i + chunk_size >= len(text):
                break
            i += step
    return out


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[dict]:
    """Deterministically split ``text`` into overlapping, boundary-aware chunks.

    ``chunk_size`` is an approximate target in characters; a chunk may exceed it
    by up to ``overlap`` when overlap context is prepended. Returns a list of
    dicts with ``text``, ``char_start``, ``char_end`` and ``chunk_index``.
    """
    if not text or not text.strip():
        return []
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = chunk_size // 4

    atoms = _hard_split(_segment(text), chunk_size, overlap)

    spans: list[tuple[int, int]] = []
    current: list[tuple[str, int, int]] = []
    for atom in atoms:
        if current and (atom[2] - current[0][1]) > chunk_size:
            spans.append((current[0][1], current[-1][2]))
            # Reseed the next chunk with the tail atoms that fall within
            # `overlap` characters of the boundary, guaranteeing forward progress.
            boundary = current[-1][2]
            seed = [a for a in current if boundary - a[1] <= overlap]
            if len(seed) == len(current):
                seed = seed[1:]
            current = seed
        current.append(atom)
    if current:
        spans.append((current[0][1], current[-1][2]))

    return [
        {
            "text": text[start:end],
            "char_start": start,
            "char_end": end,
            "chunk_index": index,
        }
        for index, (start, end) in enumerate(spans)
    ]


# ---------------------------------------------------------------------------
# Corpus assembly
# ---------------------------------------------------------------------------
def _doc_id(relative_path: str) -> str:
    """Stable, path-derived document id (survives reordering and re-runs)."""
    return hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:12]


def corpus_fingerprint(ids: list[str], texts: list[str]) -> str:
    """Content hash of the whole corpus, used to detect changes for re-indexing."""
    h = hashlib.sha256()
    for doc_id, text in zip(ids, texts):
        h.update(doc_id.encode("utf-8"))
        h.update(b"\x00")
        h.update(text.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def build_corpus(
    data_dir: str | Path,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> CorpusBuildResult:
    """Discover, parse, and chunk every document under ``data_dir``.

    Returns parallel ``texts``/``ids``/``metadatas`` arrays (ready for ChromaDB
    or FAISS) plus a content fingerprint and document/chunk counts.
    """
    root = Path(data_dir)
    paths = discover_documents(root)

    chunks: list[Chunk] = []
    num_documents = 0
    for path in paths:
        raw = load_document(path)
        if not raw or not raw.strip():
            logger.warning("Skipping empty or unreadable document: %s", path)
            continue
        relative = path.relative_to(root).as_posix()
        doc_id = _doc_id(relative)
        pieces = chunk_text(raw, chunk_size, chunk_overlap)
        if not pieces:
            continue
        num_documents += 1
        total = len(pieces)
        for piece in pieces:
            index = piece["chunk_index"]
            chunks.append(
                Chunk(
                    id=f"{doc_id}:{index}",
                    text=piece["text"],
                    metadata={
                        "doc_id": doc_id,
                        "filename": relative,
                        "doc_type": path.suffix.lower().lstrip("."),
                        "chunk_index": index,
                        "total_chunks": total,
                        "char_start": piece["char_start"],
                        "char_end": piece["char_end"],
                        "source": root.name,
                    },
                )
            )

    texts = [c.text for c in chunks]
    ids = [c.id for c in chunks]
    metadatas = [c.metadata for c in chunks]
    return CorpusBuildResult(
        texts=texts,
        ids=ids,
        metadatas=metadatas,
        fingerprint=corpus_fingerprint(ids, texts),
        num_documents=num_documents,
        num_chunks=len(chunks),
    )
