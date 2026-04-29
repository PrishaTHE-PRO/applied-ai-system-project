"""TF-IDF based retrieval over the local knowledge base."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


KB_DIR = Path(__file__).parent / "knowledge_base"


@dataclass
class RetrievedChunk:
    source: str         # filename
    text: str           # the chunk content
    score: float        # cosine similarity 0..1


class KnowledgeRetriever:
    """Loads markdown files from the KB folder and retrieves the most
    relevant ones for a query using TF-IDF + cosine similarity."""

    def __init__(self, kb_dir: Path = KB_DIR):
        self.kb_dir = kb_dir
        self.docs: List[str] = []
        self.sources: List[str] = []
        self._load()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.docs)

    def _load(self) -> None:
        for path in sorted(self.kb_dir.glob("*.md")):
            self.docs.append(path.read_text(encoding="utf-8"))
            self.sources.append(path.name)
        if not self.docs:
            raise RuntimeError(f"No knowledge base documents found in {self.kb_dir}")

    def retrieve(self, query: str, top_k: int = 2, min_score: float = 0.05) -> List[RetrievedChunk]:
        """Return the top_k most relevant chunks for the query.
        Anything below min_score is filtered out (helps catch off-topic queries)."""
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sorted(
            zip(self.sources, self.docs, sims),
            key=lambda t: t[2],
            reverse=True,
        )
        results = []
        for src, text, score in ranked[:top_k]:
            if score >= min_score:
                results.append(RetrievedChunk(source=src, text=text, score=float(score)))
        return results