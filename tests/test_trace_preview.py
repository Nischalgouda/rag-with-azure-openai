from app.trace import _preview


def test_preview_strips_markdown_heading_marks_and_collapses_whitespace():
    assert _preview("# Azure AI Search overview\n\nAzure AI Search is   managed.") == (
        "Azure AI Search overview Azure AI Search is managed."
    )


def test_preview_truncates_long_text_with_an_ellipsis():
    out = _preview("word " * 100, limit=20)
    assert out.endswith("…") and len(out) == 21


def test_preview_leaves_short_text_untouched():
    assert _preview("short") == "short"
