# ADR 003: Vector Database Selection

## Context
The Resolution Agent requires a Retrieval-Augmented Generation (RAG) pipeline to query historical incident post-mortems and runbooks based on semantic similarity and exact keyword matches.

## Alternatives Considered
1. **Pinecone:** Fully managed SaaS vector database.
2. **Milvus:** Highly scalable, open-source vector database.
3. **Qdrant:** Rust-based, open-source vector search engine.

## Tradeoffs
- Pinecone violates strict on-prem/VPC data privacy requirements for enterprise logs since it is SaaS-only.
- Milvus is incredibly powerful but requires a heavy infrastructure footprint (MinIO, etcd) for deployment.
- Qdrant is exceptionally fast, supports hybrid search natively (BM25 + Dense), and runs locally in a single Docker container.

## Decision
We will use **Qdrant**.

## Consequences
- The system remains fully containerized and air-gapped.
- We must manage a local Qdrant container and its associated persistent volumes in our DevOps pipeline.
