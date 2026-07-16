import logging
from typing import Any, List, Protocol

from src.rag.schemas import RetrievedDocument

logger = logging.getLogger(__name__)


class Reranker(Protocol):
    def rerank(
        self, query: str, documents: List[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        """Filters and strictly orders documents by semantic relevance."""
        ...


class CrossEncoderReranker:
    """
    Local Cross-Encoder using sentence-transformers.
    Air-gapped compatible (downloads model once, runs offline).
    """

    def __init__(
        self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ) -> None:
        self.model_name = model_name
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                logger.info(f"Loading local CrossEncoder: {self.model_name}")
                self._model = CrossEncoder(self.model_name)
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Falling back to Mock Reranker."
                )
                self._model = "mock"
        return self._model

    def rerank(
        self, query: str, documents: List[RetrievedDocument], top_k: int = 5
    ) -> List[RetrievedDocument]:
        if not documents:
            return []

        model = self._get_model()

        if model == "mock":
            return documents[:top_k]

        pairs = [[query, doc.content] for doc in documents]
        scores = model.predict(pairs)

        for doc, score in zip(documents, scores):
            doc.citation.relevance_score = float(score)

        documents.sort(key=lambda x: x.citation.relevance_score, reverse=True)
        return documents[:top_k]
