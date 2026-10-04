from app.keyword import bm25_scores


def test_exact_term_ranks_its_document_first():
    docs = ["cats and dogs", "error code E1234 occurred", "weather is nice"]
    scores = bm25_scores("E1234", docs)
    assert scores.argmax() == 1 and scores[0] == 0


def test_no_matching_terms_scores_zero():
    assert bm25_scores("zzz", ["abc", "def"]).sum() == 0
