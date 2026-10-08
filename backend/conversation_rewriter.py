import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


MODEL = "openai/gpt-oss-120b"


def rewrite_conversation_query(
    question: str,
    conversation: list[dict] | None = None
) -> str:
    """
    Rewrite a follow-up question into a standalone
    search query using recent conversation context.
    """

    if not conversation:
        return question

    conversation_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in conversation[-6:]
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
Rewrite the user's latest question into a
standalone search query.

Use the conversation history to resolve references
such as:
- it
- they
- them
- this
- that
- the company
- the policy

Rules:
1. Preserve the user's intended meaning.
2. Do not answer the question.
3. Do not add unsupported information.
4. Return only the standalone search query.
"""
            },
            {
                "role": "user",
                "content": f"""
Conversation history:

{conversation_text}

Latest question:

{question}
"""
            }
        ],
        temperature=0
    )

    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )