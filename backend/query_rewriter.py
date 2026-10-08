import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


MODEL = "openai/gpt-oss-120b"


def rewrite_query(question: str) -> str:
    """
    Rewrite a user question into a concise
    search query suitable for document retrieval.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You rewrite user questions for document retrieval.

Rules:
1. Preserve the original meaning.
2. Make the query concise and specific.
3. Do not answer the question.
4. Do not add information that is not present
   in the original question.
5. Return only the rewritten query.
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0
    )

    rewritten_query = (
        response.choices[0]
        .message
        .content
        .strip()
    )

    return rewritten_query