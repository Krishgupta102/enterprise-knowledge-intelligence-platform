from sentence_transformers import SentenceTransformer
import numpy as np


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def rerank_chunks(
    query: str,
    chunks: list,
    top_k: int = 3
):
    """
    Simple reranking using cosine similarity
    between the query and retrieved chunks.

    Expected chunk format:
    (
        chunk_id,
        document_id,
        chunk_index,
        content,
        vector_score,
        keyword_score,
        hybrid_score,
        filename,
        file_type,
        title
    )
    """

    if not chunks:
        return []

    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True
    )

    contents = [
        chunk[3]
        for chunk in chunks
    ]

    chunk_embeddings = embedding_model.encode(
        contents,
        normalize_embeddings=True
    )

    scores = np.dot(
        chunk_embeddings,
        query_embedding
    )

    reranked = []

    for chunk, score in zip(
        chunks,
        scores
    ):

        reranked.append(
            (
                chunk,
                float(score)
            )
        )

    reranked.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return [
        item[0]
        for item in reranked[:top_k]
    ]