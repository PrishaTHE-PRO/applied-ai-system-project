from ai.retriever import KnowledgeRetriever


def test_feeding_query_retrieves_feeding_doc():
    r = KnowledgeRetriever()
    chunks = r.retrieve("how often should I feed my dog")
    assert chunks, "expected at least one chunk"
    assert chunks[0].source == "feeding.md"


def test_exercise_query_retrieves_exercise_doc():
    r = KnowledgeRetriever()
    chunks = r.retrieve("how long should I walk my border collie")
    assert chunks[0].source == "exercise.md"


def test_offtopic_query_filters_out():
    r = KnowledgeRetriever()
    chunks = r.retrieve("capital of france", min_score=0.2)
    assert chunks == []