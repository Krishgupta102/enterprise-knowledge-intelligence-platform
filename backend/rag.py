import os

from dotenv import load_dotenv
from openai import OpenAI

from query_rewriter import rewrite_query
from reranker import rerank_chunks
from retriever import retrieve_chunks
from conversation_rewriter import rewrite_conversation_query

load_dotenv()


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


MODEL = "openai/gpt-oss-120b"


def generate_answer(
    question: str,
    file_type: str | None = None,
    document_id: int | None = None,
    conversation: list[dict] | None = None
):
    """
    Generate an answer using:

    1. Query rewriting
    2. Hybrid retrieval
    3. Reranking
    4. LLM generation
    """

    # --------------------------------
    # 1. Rewrite query
    # --------------------------------

    search_query = rewrite_conversation_query(
        question,
        conversation
    )

    print(
        f"\nOriginal query: {question}"
    )

    print(
        f"Search query: {search_query}"
    )

    # --------------------------------
    # 2. Retrieve relevant chunks
    # --------------------------------

    results = retrieve_chunks(
        query=search_query,
        top_k=5,
        file_type=file_type,
        document_id=document_id
    )

    # --------------------------------
    # 3. Rerank retrieved chunks
    # --------------------------------

    results = rerank_chunks(
        query=search_query,
        chunks=results,
        top_k=3
    )

    # --------------------------------
    # 4. Handle no results
    # --------------------------------

    if not results:

        return {
            "answer": (
                "I couldn't find relevant information "
                "in the available documents."
            ),
            "sources": []
        }

    # --------------------------------
    # 5. Build context
    # --------------------------------

    context_parts = []

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

        context_parts.append(
            f"""
[Source: {title or filename}
File: {filename}
Chunk: {chunk_index}
Hybrid Score: {hybrid_score:.4f}]

{content}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    # --------------------------------
    # 6. System prompt
    # --------------------------------

    system_prompt = """
You are an enterprise knowledge assistant.

Answer the user's question using ONLY
the provided context.

Rules:

1. Do not use outside knowledge.
2. If the context does not contain the answer,
   say you don't know.
3. Keep the answer concise and factual.
4. Do not invent information.
5. Prefer information from the highest-ranked
   relevant sources.
6. Do not mention retrieval scores unless
   the user explicitly asks about them.
"""

    # --------------------------------
    # 7. User prompt
    # --------------------------------

    user_prompt = f"""
Context:

{context}

Question:

{question}
"""

    # --------------------------------
    # 8. Generate answer
    # --------------------------------

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0
    )

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    # --------------------------------
    # 9. Return answer + sources
    # --------------------------------

    return {
        "answer": answer,

        "sources": [
            {
                "document_id": result[1],
                "title": result[9],
                "document": result[7],
                "file_type": result[8],
                "chunk_id": result[0],
                "chunk_index": result[2],
                "vector_score": float(result[4]),
                "keyword_score": float(result[5]),
                "hybrid_score": float(result[6]),
                "content": result[3]
            }
            for result in results
        ]
    }


if __name__ == "__main__":

    question = (
        "What security requirements "
        "do employees have?"
    )

    # --------------------------------
    # TEST 1
    # Query rewriting + Hybrid RAG
    # --------------------------------

    result = generate_answer(
        question
    )

    print("\n" + "=" * 70)
    print("TEST 1: QUERY REWRITING + HYBRID RAG")
    print("=" * 70)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:

        print(
            "\n" + "-" * 70
        )

        print(
            f"Document: "
            f"{source['title']}"
        )

        print(
            f"Vector Score: "
            f"{source['vector_score']:.4f}"
        )

        print(
            f"Keyword Score: "
            f"{source['keyword_score']:.4f}"
        )

        print(
            f"Hybrid Score: "
            f"{source['hybrid_score']:.4f}"
        )

    # --------------------------------
    # TEST 2
    # File type filter
    # --------------------------------

    result = generate_answer(
        question,
        file_type=".txt"
    )

    print("\n" + "=" * 70)
    print("TEST 2: QUERY REWRITING + FILE FILTER")
    print("=" * 70)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:

        print(
            f"{source['title']} "
            f"| {source['file_type']} "
            f"| Hybrid: "
            f"{source['hybrid_score']:.4f}"
        )

    # --------------------------------
    # TEST 3
    # Document filter
    # --------------------------------

    result = generate_answer(
        question,
        document_id=3
    )

    print("\n" + "=" * 70)
    print(
        "TEST 3: QUERY REWRITING "
        "+ DOCUMENT FILTER"
    )
    print("=" * 70)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")

    for source in result["sources"]:

        print(
            f"{source['title']} "
            f"| Document ID: "
            f"{source['document_id']} "
            f"| Hybrid: "
            f"{source['hybrid_score']:.4f}"
        )