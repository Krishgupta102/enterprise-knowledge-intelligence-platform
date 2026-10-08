import json
import sys
from pathlib import Path


# --------------------------------
# Add backend directory to Python path
# --------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent

sys.path.append(
    str(BACKEND_DIR)
)


from retriever import retrieve_chunks


# --------------------------------
# Load evaluation dataset
# --------------------------------

DATASET_PATH = (
    Path(__file__).parent
    / "eval_dataset.json"
)


with open(
    DATASET_PATH,
    "r",
    encoding="utf-8"
) as file:

    dataset = json.load(file)


# --------------------------------
# Evaluation configuration
# --------------------------------

TOP_K_VALUES = [1, 3]


# --------------------------------
# Evaluation
# --------------------------------

results = []


for item in dataset:

    question = item["question"]

    expected_document_id = (
        item["expected_document_id"]
    )

    retrieved_chunks = retrieve_chunks(
        query=question,
        top_k=max(TOP_K_VALUES)
    )

    retrieved_document_ids = [
        result[1]
        for result in retrieved_chunks
    ]

    # --------------------------------
    # Get top hybrid score
    # --------------------------------

    top_hybrid_score = None

    if retrieved_chunks:

        top_hybrid_score = float(
            retrieved_chunks[0][6]
        )

    # --------------------------------
    # Remove duplicate document IDs
    # --------------------------------

    unique_document_ids = list(
        dict.fromkeys(
            retrieved_document_ids
        )
    )

    # --------------------------------
    # Handle unanswerable questions
    # --------------------------------

    if expected_document_id is None:

        # For an unanswerable question,
        # retrieval is considered successful
        # only if no documents are returned.

        no_relevant_documents = (
            len(retrieved_chunks) == 0
        )

        results.append(
            {
                "question": question,
                "expected_document_id": None,
                "retrieved_document_ids":
                    unique_document_ids,
                "top_hybrid_score":
                    top_hybrid_score,
                "unanswerable": True,
                "correct_rejection":
                    no_relevant_documents
            }
        )

        continue

    # --------------------------------
    # Answerable question
    # --------------------------------

    recall_scores = {}

    for k in TOP_K_VALUES:

        top_k_documents = (
            unique_document_ids[:k]
        )

        recall_scores[
            f"recall@{k}"
        ] = (
            1
            if expected_document_id
            in top_k_documents
            else 0
        )

    results.append(
        {
            "question": question,
            "expected_document_id":
                expected_document_id,
            "retrieved_document_ids":
                unique_document_ids,
            "top_hybrid_score":
                top_hybrid_score,
            "unanswerable": False,
            **recall_scores
        }
    )


# --------------------------------
# Separate answerable / unanswerable
# --------------------------------

answerable_results = [
    result
    for result in results
    if not result["unanswerable"]
]


unanswerable_results = [
    result
    for result in results
    if result["unanswerable"]
]


# --------------------------------
# Calculate recall
# --------------------------------

metrics = {}

if answerable_results:

    for k in TOP_K_VALUES:

        metric_name = f"recall@{k}"

        score = sum(
            result[metric_name]
            for result in answerable_results
        )

        metrics[metric_name] = (
            score
            / len(answerable_results)
        )


# --------------------------------
# Calculate correct rejection
# --------------------------------

if unanswerable_results:

    correct_rejections = sum(
        result["correct_rejection"]
        for result in unanswerable_results
    )

    metrics["correct_rejection_rate"] = (
        correct_rejections
        / len(unanswerable_results)
    )


# --------------------------------
# Print detailed results
# --------------------------------

print("\n" + "=" * 70)
print("RAG RETRIEVAL EVALUATION")
print("=" * 70)


for result in results:

    print("\n" + "-" * 70)

    print(
        f"Question: "
        f"{result['question']}"
    )

    print(
        f"Expected document: "
        f"{result['expected_document_id']}"
    )

    if result["top_hybrid_score"] is not None:

        print(
            f"Top hybrid score: "
            f"{result['top_hybrid_score']:.4f}"
        )

    else:

        print(
            "Top hybrid score: None"
        )

    print(
        f"Retrieved documents: "
        f"{result['retrieved_document_ids']}"
    )

    if result["unanswerable"]:

        print(
            f"Correct rejection: "
            f"{result['correct_rejection']}"
        )

    else:

        print(
            f"Recall@1: "
            f"{result['recall@1']}"
        )

        print(
            f"Recall@3: "
            f"{result['recall@3']}"
        )


# --------------------------------
# Print overall metrics
# --------------------------------

print("\n" + "=" * 70)
print("OVERALL METRICS")
print("=" * 70)


for metric, score in metrics.items():

    print(
        f"{metric}: "
        f"{score:.2%}"
    )


print(
    f"\nTotal questions: "
    f"{len(results)}"
)

print(
    f"Answerable questions: "
    f"{len(answerable_results)}"
)

print(
    f"Unanswerable questions: "
    f"{len(unanswerable_results)}"
)