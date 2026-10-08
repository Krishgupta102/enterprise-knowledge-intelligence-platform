from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------
# Load Embedding Model
# -----------------------------

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# -----------------------------
# Test Texts
# -----------------------------

texts = [
    "Our company provides 20 days of annual leave.",
    "Employees receive twenty vacation days each year.",
    "The company uses PostgreSQL for its database."
]


# -----------------------------
# Generate Embeddings
# -----------------------------

embeddings = model.encode(
    texts
)


print(
    "Number of embeddings:",
    len(embeddings)
)

print(
    "Vector dimensions:",
    len(embeddings[0])
)


# -----------------------------
# Calculate Similarity
# -----------------------------

similarity_matrix = cosine_similarity(
    embeddings
)


print("\nSimilarity Matrix:")
print(similarity_matrix)


# -----------------------------
# Compare Specific Sentences
# -----------------------------

print("\nComparisons:")

print(
    "Annual leave vs vacation:",
    similarity_matrix[0][1]
)

print(
    "Annual leave vs PostgreSQL:",
    similarity_matrix[0][2]
)