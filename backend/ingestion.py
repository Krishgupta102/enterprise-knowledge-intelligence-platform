from pathlib import Path

from sentence_transformers import SentenceTransformer

from document_loader import load_document
from chunker import chunk_text
from database import get_connection


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def generate_title(path: Path) -> str:
    """
    Generate a readable document title from the filename.

    Example:
    employee-handbook.pdf
    -> Employee Handbook
    """

    return path.stem.replace("_", " ").replace("-", " ").title()


def ingest_document(file_path: str):

    path = Path(file_path)

    print(f"Processing document: {path.name}")

    # -----------------------------
    # 1. Load document
    # -----------------------------

    text = load_document(file_path)

    if not text.strip():
        raise ValueError("Document is empty")

    # -----------------------------
    # 2. Extract metadata
    # -----------------------------

    file_type = path.suffix.lower()
    title = generate_title(path)

    print(f"Title: {title}")
    print(f"File type: {file_type}")

    # -----------------------------
    # 3. Create chunks
    # -----------------------------

    chunks = chunk_text(
        text,
        chunk_size=500,
        overlap=1
    )

    if not chunks:
        raise ValueError(
            "No chunks were generated"
        )

    print(
        f"Generated {len(chunks)} chunks"
    )

    # -----------------------------
    # 4. Generate embeddings
    # -----------------------------

    embeddings = embedding_model.encode(
        chunks
    )

    print(
        f"Generated embeddings with dimension: "
        f"{len(embeddings[0])}"
    )

    # -----------------------------
    # 5. Store in PostgreSQL
    # -----------------------------

    with get_connection() as conn:

        with conn.cursor() as cur:

            # Insert document + metadata
            cur.execute(
                """
                INSERT INTO documents
                    (
                        filename,
                        content,
                        file_type,
                        title
                    )
                VALUES
                    (%s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    path.name,
                    text,
                    file_type,
                    title
                )
            )

            document_id = cur.fetchone()[0]

            # Insert chunks
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                cur.execute(
                    """
                    INSERT INTO document_chunks
                        (document_id, chunk_index, content, embedding, search_vector)
                    VALUES
                        (%s, %s, %s, %s, to_tsvector('english', %s));
                    """,
                    (
                        document_id,
                        index,
                        chunk,
                        embedding.tolist(),
                        chunk
                    )
                )

        conn.commit()

    print(
        f"Document '{path.name}' "
        f"successfully indexed with ID {document_id}"
    )

    return {
        "document_id": document_id,
        "filename": path.name,
        "file_type": file_type,
        "title": title,
        "characters": len(text),
        "chunks": len(chunks)
    }


if __name__ == "__main__":

    result = ingest_document(
        "documents/company-policy.txt"
    )

    print("\nIngestion result:")
    print(result)