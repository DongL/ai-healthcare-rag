"""Unit tests for the ingestion pipeline (pure functions, no model or network)."""
import pytest

import ingest


def _write(directory, name, content):
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# discover_documents
# ---------------------------------------------------------------------------
def test_discover_finds_supported_sorted_recursive(tmp_path):
    _write(tmp_path, "b.md", "x")
    _write(tmp_path, "a.txt", "y")
    _write(tmp_path, "ignore.csv", "z")  # unsupported extension
    (tmp_path / "sub").mkdir()
    _write(tmp_path / "sub", "c.md", "w")

    found = ingest.discover_documents(tmp_path)

    assert [p.name for p in found] == ["a.txt", "b.md", "c.md"]


def test_discover_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest.discover_documents(tmp_path / "does_not_exist")


def test_discover_not_a_directory_raises(tmp_path):
    f = _write(tmp_path, "a.md", "x")
    with pytest.raises(NotADirectoryError):
        ingest.discover_documents(f)


# ---------------------------------------------------------------------------
# load_document
# ---------------------------------------------------------------------------
def test_load_txt_and_md_read_directly(tmp_path):
    p = _write(tmp_path, "a.md", "# Title\n\nBody text.")
    assert ingest.load_document(p) == "# Title\n\nBody text."


def test_load_unsupported_extension_raises(tmp_path):
    p = _write(tmp_path, "a.csv", "x,y,z")
    with pytest.raises(ValueError):
        ingest.load_document(p)


# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------
def test_chunk_empty_and_whitespace_return_empty():
    assert ingest.chunk_text("") == []
    assert ingest.chunk_text("   \n\n  ") == []


def test_chunk_single_short_sentence():
    chunks = ingest.chunk_text("The heart pumps blood.", chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "The heart pumps blood."
    assert chunks[0]["chunk_index"] == 0


def test_chunk_offsets_reconstruct_text_exactly():
    text = (
        "Sentence one is here. Sentence two follows. Sentence three ends it. "
        "A fourth sentence adds more content. And a fifth to be sure of it."
    )
    chunks = ingest.chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) > 1
    for c in chunks:
        # Core invariant: a chunk can always be located back in its source.
        assert text[c["char_start"] : c["char_end"]] == c["text"]


def test_chunk_indices_are_sequential():
    text = " ".join(f"Sentence number {i} here." for i in range(30))
    chunks = ingest.chunk_text(text, chunk_size=60, overlap=15)
    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_chunk_size_is_approximately_bounded():
    text = " ".join(f"Sentence number {i} is here." for i in range(50))
    size, overlap = 80, 20
    chunks = ingest.chunk_text(text, chunk_size=size, overlap=overlap)
    for c in chunks:
        # chunk_size is a soft target; overlap context + separators may push a
        # chunk slightly over, but never unboundedly.
        assert len(c["text"]) <= size + overlap + 16


def test_chunk_consecutive_chunks_overlap():
    text = " ".join(f"Sentence number {i} is here." for i in range(40))
    chunks = ingest.chunk_text(text, chunk_size=80, overlap=30)
    assert len(chunks) > 1
    overlaps = [
        chunks[i + 1]["char_start"] < chunks[i]["char_end"]
        for i in range(len(chunks) - 1)
    ]
    assert any(overlaps)


def test_chunk_hard_splits_oversized_atom():
    text = "x" * 1000  # a single "sentence" with no natural boundaries
    chunks = ingest.chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c["text"]) <= 100


# ---------------------------------------------------------------------------
# build_corpus
# ---------------------------------------------------------------------------
def test_build_corpus_basic_shape(tmp_path):
    _write(
        tmp_path,
        "cardio.md",
        "# Hypertension\n\nBlood pressure should be monitored. Lifestyle changes help.",
    )
    _write(
        tmp_path,
        "endo.md",
        "# Diabetes\n\nMetformin is a first-line therapy. It lowers blood glucose.",
    )
    result = ingest.build_corpus(tmp_path, chunk_size=512, chunk_overlap=64)

    assert result.num_documents == 2
    assert result.num_chunks >= 2
    assert len(result.texts) == result.num_chunks
    assert len(result.ids) == result.num_chunks
    assert len(result.metadatas) == result.num_chunks
    assert len(set(result.ids)) == result.num_chunks  # ids are unique

    md = result.metadatas[0]
    for key in (
        "doc_id",
        "filename",
        "doc_type",
        "chunk_index",
        "total_chunks",
        "char_start",
        "char_end",
        "source",
    ):
        assert key in md
    assert md["doc_type"] == "md"


def test_build_corpus_metadata_values_are_scalar(tmp_path):
    # ChromaDB only accepts str/int/float/bool metadata values.
    _write(tmp_path, "a.md", "# Topic\n\nSome content here that is long enough to chunk.")
    result = ingest.build_corpus(tmp_path)
    for md in result.metadatas:
        for value in md.values():
            assert isinstance(value, (str, int, float, bool))


def test_build_corpus_fingerprint_stable_and_change_sensitive(tmp_path):
    _write(tmp_path, "a.md", "# Topic\n\nStable content.")
    fp1 = ingest.build_corpus(tmp_path).fingerprint
    fp2 = ingest.build_corpus(tmp_path).fingerprint
    assert fp1 == fp2  # deterministic across runs

    _write(tmp_path, "a.md", "# Topic\n\nChanged content now.")
    fp3 = ingest.build_corpus(tmp_path).fingerprint
    assert fp3 != fp1  # sensitive to content changes


def test_build_corpus_empty_dir(tmp_path):
    result = ingest.build_corpus(tmp_path)
    assert result.num_chunks == 0
    assert result.texts == []
    assert result.fingerprint == ingest.corpus_fingerprint([], [])
