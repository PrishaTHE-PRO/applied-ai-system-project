"""Claude-powered RAG assistant for PawPal+."""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List

from anthropic import Anthropic
from dotenv import load_dotenv

from ai.retriever import KnowledgeRetriever, RetrievedChunk
from ai.guardrails import is_unsafe_request
from ai.logger import get_logger


load_dotenv()

CLAUDE_MODEL = "claude-haiku-4-5-20251001"  # fast + cheap, perfect for this assignment

SYSTEM_PROMPT = """You are PawPal AI, a friendly assistant that helps pet owners
with general pet care questions. You answer ONLY using the context provided
to you. If the context does not contain the answer, say:
"I don't have reliable information on that — please ask a vet."

Always:
- Cite which source file your answer came from at the end (e.g., "Source: feeding.md").
- Refuse to diagnose illness or recommend medication dosages.
- Recommend a vet for any urgent or medical question.
"""


@dataclass
class AssistantAnswer:
    answer: str
    sources: List[str]
    confidence: float           # average retrieval score
    refused: bool               # True if guardrail or low-confidence refusal
    log_id: str


class PawPalAssistant:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.retriever = KnowledgeRetriever()
        self.logger = get_logger("assistant")

    def ask(self, question: str, min_confidence: float = 0.05) -> AssistantAnswer:
        log_id = self.logger.start(question)

        # Guardrail 1: refuse unsafe categories before spending tokens
        if is_unsafe_request(question):
            answer = ("I can't help with diagnosing illness or medication dosages. "
                      "Please contact a licensed veterinarian.")
            self.logger.finish(log_id, answer=answer, refused=True, sources=[], confidence=0.0)
            return AssistantAnswer(answer=answer, sources=[], confidence=0.0,
                                   refused=True, log_id=log_id)

        # Retrieve grounding context
        chunks: List[RetrievedChunk] = self.retriever.retrieve(question, top_k=2)
        confidence = (sum(c.score for c in chunks) / len(chunks)) if chunks else 0.0

        # Guardrail 2: low-confidence refusal (off-topic queries)
        if confidence < min_confidence or not chunks:
            answer = ("I don't have reliable information on that in my knowledge base. "
                      "Please ask a vet.")
            self.logger.finish(log_id, answer=answer, refused=True, sources=[],
                               confidence=confidence)
            return AssistantAnswer(answer=answer, sources=[], confidence=confidence,
                                   refused=True, log_id=log_id)

        context_block = "\n\n".join(
            f"[Source: {c.source}]\n{c.text}" for c in chunks
        )
        user_message = (
            f"Context from PawPal's pet-care knowledge base:\n\n{context_block}\n\n"
            f"Question: {question}\n\n"
            f"Answer using ONLY the context above."
        )

        msg = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        answer = msg.content[0].text.strip()

        sources = [c.source for c in chunks]
        self.logger.finish(log_id, answer=answer, refused=False, sources=sources,
                           confidence=confidence)
        return AssistantAnswer(answer=answer, sources=sources, confidence=confidence,
                               refused=False, log_id=log_id)