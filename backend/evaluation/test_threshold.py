import sys
from pathlib import Path


# --------------------------------
# Add backend directory to path
# --------------------------------

BACKEND_DIR = (
    Path(__file__).resolve().parent.parent
)

sys.path.append(
    str(BACKEND_DIR)
)


from retriever import retrieve_chunks


# --------------------------------
# Questions with no answer
# --------------------------------

questions = [
    "What database does the company use?",
    "What programming language does the company use?"
]


# --------------------------------
# Test
# --------------------------------

for question in questions:

    print("\n" + "=" * 70)

    print(
        f"Question: {question}"
    )

    print("=" * 70)

    results = retrieve_chunks(
        query=question,
        top_k=3
    )

    for index, result in enumerate(
        results,
        start=1
    ):

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

        print(
            f"\nRank {index}"
        )

        print(
            f"Document: {filename}"
        )

        print(
            f"Vector score: "
            f"{vector_score:.4f}"
        )

        print(
            f"Keyword score: "
            f"{keyword_score:.10f}"
        )

        print(
            f"Hybrid score: "
            f"{hybrid_score:.4f}"
        )

        print(
            f"Content: {content}"
        )