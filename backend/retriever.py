from sentence_transformers import SentenceTransformer

from database import get_connection


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

SIMILARITY_THRESHOLD = 0.40

VECTOR_WEIGHT = 0.70
KEYWORD_WEIGHT = 0.30

KEYWORD_THRESHOLD = 0.001
ABSTENTION_THRESHOLD = 0.30


def retrieve_chunks(
    query: str,
    top_k: int = 3,
    file_type: str | None = None,
    document_id: int | None = None
):
    """
    Hybrid retrieval using:

    1. Vector similarity
    2. PostgreSQL full-text search
    3. Optional metadata filters

    A chunk becomes a candidate when either:
    - vector similarity is above SIMILARITY_THRESHOLD
    - keyword relevance is above KEYWORD_THRESHOLD
    """

    query_embedding = embedding_model.encode(query)
    embedding = query_embedding.tolist()

    metadata_conditions = []
    metadata_parameters = []

    if file_type is not None:
        metadata_conditions.append(
            "d.file_type = %s"
        )
        metadata_parameters.append(file_type)

    if document_id is not None:
        metadata_conditions.append(
            "d.id = %s"
        )
        metadata_parameters.append(document_id)

    metadata_clause = ""

    if metadata_conditions:
        metadata_clause = (
            "AND "
            + " AND ".join(metadata_conditions)
        )

    sql = f"""
        SELECT
            dc.id,
            dc.document_id,
            dc.chunk_index,
            dc.content,

            1 - (
                dc.embedding <=> %s::vector
            ) AS vector_score,

            ts_rank(
                dc.search_vector,
                plainto_tsquery(
                    'english',
                    %s
                )
            ) AS keyword_score,

            (
                %s * (
                    1 - (
                        dc.embedding <=> %s::vector
                    )
                )
                +
                %s * ts_rank(
                    dc.search_vector,
                    plainto_tsquery(
                        'english',
                        %s
                    )
                )
            ) AS hybrid_score,

            d.filename,
            d.file_type,
            d.title

        FROM document_chunks dc

        JOIN documents d
            ON dc.document_id = d.id

        WHERE
            (
                (
                    1 - (
                        dc.embedding <=> %s::vector
                    )
                ) >= %s

                OR

                ts_rank(
                    dc.search_vector,
                    plainto_tsquery(
                        'english',
                        %s
                    )
                ) >= %s
            )

            {metadata_clause}

        ORDER BY
            hybrid_score DESC

        LIMIT %s;
    """

    parameters = [
        # vector_score
        embedding,

        # keyword_score
        query,

        # hybrid vector component
        VECTOR_WEIGHT,
        embedding,

        # hybrid keyword component
        KEYWORD_WEIGHT,
        query,

        # candidate vector threshold
        embedding,
        SIMILARITY_THRESHOLD,

        # candidate keyword threshold
        query,
        KEYWORD_THRESHOLD
    ]

    parameters.extend(metadata_parameters)

    parameters.append(top_k)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                parameters
            )

            results = cur.fetchall()

    if not results:
        return []

    top_score = float(results[0][6])

    if top_score < ABSTENTION_THRESHOLD:
        return []

    return results


if __name__ == "__main__":

    query = (
        "What security requirements "
        "do employees have?"
    )

    results = retrieve_chunks(query)

    print("\n" + "=" * 70)
    print("TEST: HYBRID SEARCH")
    print("=" * 70)

    print(f"\nQuery: {query}")

    if not results:
        print("\nNo relevant information found.")

    for result in results:

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
        ) = result

        print("\n" + "-" * 70)

        print(f"Document ID: {document_id}")
        print(f"Title: {title}")
        print(f"Filename: {filename}")
        print(f"File Type: {file_type}")
        print(f"Chunk ID: {chunk_id}")

        print(
            f"Vector Score: "
            f"{vector_score:.4f}"
        )

        print(
            f"Keyword Score: "
            f"{keyword_score:.4f}"
        )

        print(
            f"Hybrid Score: "
            f"{hybrid_score:.4f}"
        )

        print("\nContent:")
        print(content)