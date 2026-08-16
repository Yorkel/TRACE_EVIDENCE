"""Fast, data-free preprocessing regression tests."""
from trace_evidence.preprocessing import clean_doc, chunk_doc, prepare, load_boilerplate


def test_clean_doc_strips_wordpress_markup():
    t = "[vc_row][vc_column] The Minister spoke. Email [email protected] visit wwwgovuk. cssvc_custom_99 alignmentcenter A real sentence about Ofsted."
    c = clean_doc(t)
    assert "vc_row" not in c and "vc_column" not in c
    assert "email protected" not in c.lower()
    assert "cssvc" not in c.lower() and "wwwgovuk" not in c
    assert "real sentence about Ofsted" in c


def test_clean_doc_strips_frozen_boilerplate_line():
    boiler = next(iter(load_boilerplate()))
    t = f"{boiler}\nGenuine content about schools and funding follows here."
    c = clean_doc(t)
    assert boiler not in c
    assert "Genuine content" in c


def test_chunk_doc_caps_at_40():
    text = ". ".join(f"sentence {i} with several words in it" for i in range(600))
    chunks = chunk_doc(text, target=100, cap=40)
    assert 1 <= len(chunks) <= 40
    assert all(isinstance(ch, str) and ch for ch in chunks)


def test_chunk_doc_short_text_one_chunk():
    chunks = chunk_doc("A short single sentence about education.", target=100)
    assert len(chunks) == 1


def test_prepare_cleans_then_chunks():
    chunks = prepare("[vc_row] Ofsted reform of school inspection and accountability. " * 15)
    assert len(chunks) >= 1
    assert all("vc_row" not in ch for ch in chunks)
