import re


def split_into_sentences(text: str) -> list[str]:

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 1
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    sentences = split_into_sentences(text)

    chunks = []

    current_chunk = []

    for sentence in sentences:

        candidate = " ".join(
            current_chunk + [sentence]
        )

        if (
            current_chunk
            and len(candidate) > chunk_size
        ):

            chunks.append(
                " ".join(current_chunk)
            )

            current_chunk = (
                current_chunk[-overlap:]
            )

        current_chunk.append(sentence)

    if current_chunk:

        chunks.append(
            " ".join(current_chunk)
        )

    return chunks