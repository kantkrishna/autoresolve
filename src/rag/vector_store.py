# src/rag/vector_store.py
import logging
from typing import Any

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient, models

from src.core.config import settings

logger = logging.getLogger(__name__)

# Enterprise Hybrid Search Configuration
COLLECTION_NAME = "enterprise_runbooks"

# Dense Embeddings (Semantic meaning)
dense_embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
# Sparse Embeddings (Exact keyword match - BM25)
sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")


def get_qdrant_client() -> QdrantClient:
    """Connect to the Qdrant Docker container via config."""
    # Note the str() cast here to satisfy Qdrant's SDK
    return QdrantClient(url=str(settings.QDRANT_URL))


def setup_collection() -> None:
    """Creates the Qdrant collection configured for Hybrid Search."""
    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        logger.info(f"Creating hybrid collection: {COLLECTION_NAME}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(size=384, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )


def get_vector_store() -> QdrantVectorStore:
    """Returns the LangChain Qdrant integration configured for Hybrid Retrieval."""
    setup_collection()

    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=COLLECTION_NAME,
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name="dense",
        sparse_vector_name="sparse",
    )


def ingest_document(text: str, metadata: dict[str, Any]) -> None:
    """Chunks and embeds a document into both Dense and Sparse vector space."""
    store = get_vector_store()
    doc = Document(page_content=text, metadata=metadata)
    # FastEmbed automatically handles computing both vector types
    store.add_documents([doc])
    logger.info("Successfully ingested document into Qdrant.")
