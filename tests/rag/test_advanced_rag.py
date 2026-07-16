from typing import List

from src.rag.pipeline import EnterpriseRAGPipeline
from src.rag.schemas import Citation, RetrievedDocument


class MockVDB:
    def mock_hybrid_search(self, query: str) -> List[RetrievedDocument]:
        return [
            RetrievedDocument(
                content="Increase deployment memory to 2Gi to fix OOMKilled.",
                citation=Citation(
                    source="runbook-oom.md", chunk_id="chunk-1", relevance_score=0.0
                ),
            ),
            RetrievedDocument(
                content="Unrelated doc about database indexing.",
                citation=Citation(
                    source="db-tuning.md", chunk_id="chunk-2", relevance_score=0.0
                ),
            ),
        ]


def test_rag_pipeline_scores_and_filters() -> None:
    pipeline = EnterpriseRAGPipeline(vector_db_client=MockVDB())
    docs, confidence = pipeline.query_runbooks("How to fix OOMKilled exception?")

    assert len(docs) <= 5
    assert confidence.composite_score >= 0.0
    assert confidence.is_actionable is False
    assert confidence.evidence_quality == "low"
