import os
import json

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    HTTPException,
    File,
    UploadFile
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from openai import OpenAI
from pydantic import BaseModel

from database import get_connection
from ingestion import ingest_document
from rag import generate_answer


# --------------------------------
# Load environment variables
# --------------------------------

load_dotenv()


# --------------------------------
# FastAPI Application
# --------------------------------

app = FastAPI(
    title="Enterprise Knowledge Platform",
    version="0.1.0"
)


# --------------------------------
# CORS
# --------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------
# Groq Configuration
# --------------------------------

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not configured"
    )


client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1"
)


# --------------------------------
# Document Storage
# --------------------------------

DOCUMENTS_DIR = Path("documents")

DOCUMENTS_DIR.mkdir(
    exist_ok=True
)


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx"
}


# --------------------------------
# Request / Response Models
# --------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    answer: str
    topic: str
    needs_retrieval: bool


class RAGRequest(BaseModel):
    question: str
    file_type: str | None = None
    document_id: int | None = None
    conversation: list[dict] | None = None


# --------------------------------
# Basic Routes
# --------------------------------

@app.get("/")
def root():

    return {
        "message": (
            "Enterprise Knowledge Platform API "
            "is running"
        )
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# --------------------------------
# Normal Chat
# --------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful technical assistant."
                )
            }
        ]

        # Add conversation history
        messages.extend(
            message.model_dump()
            for message in request.messages
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# Streaming Chat
# --------------------------------

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful technical assistant."
            )
        }
    ]

    # Add conversation history
    messages.extend(
        message.model_dump()
        for message in request.messages
    )

    def generate():

        try:

            stream = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                stream=True
            )

            for chunk in stream:

                content = (
                    chunk.choices[0]
                    .delta
                    .content
                )

                if content:
                    yield content

        except Exception as e:

            yield f"\n[ERROR] {str(e)}"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


# --------------------------------
# Structured Chat
# --------------------------------

@app.post(
    "/chat/structured",
    response_model=ChatResponse
)
def chat_structured(request: ChatRequest):

    try:

        messages = [
            {
                "role": "system",
                "content": """
You are a helpful technical assistant.

Return your response as valid JSON with exactly these fields:

{
    "answer": "your answer",
    "topic": "main topic of the question",
    "needs_retrieval": true
}

Rules:

1. answer:
   Provide a helpful answer to the user's question.

2. topic:
   Identify the main topic of the user's question.

3. needs_retrieval:
   Set this to true if the question would benefit from
   information retrieved from an external knowledge base.

   Set this to false if the question can be answered
   using general knowledge.

Return ONLY valid JSON.
Do not include markdown.
Do not include ```json.
"""
            }
        ]

        # Add conversation history
        messages.extend(
            message.model_dump()
            for message in request.messages
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={
                "type": "json_object"
            }
        )

        raw_content = (
            response
            .choices[0]
            .message
            .content
        )

        if not raw_content:

            raise ValueError(
                "LLM returned an empty response"
            )

        # Convert JSON string into Python dictionary
        structured_data = json.loads(
            raw_content
        )

        # Validate using Pydantic
        validated_response = ChatResponse(
            **structured_data
        )

        return validated_response

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail="LLM returned invalid JSON"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# RAG
# --------------------------------

@app.post("/rag")
def rag(request: RAGRequest):

    try:

        if not request.question.strip():

            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )

        result = generate_answer(
            question=request.question,
            file_type=request.file_type,
            document_id=request.document_id,
            conversation=request.conversation
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# Document Upload
# --------------------------------

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    try:

        # --------------------------------
        # 1. Validate filename
        # --------------------------------

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )

        filename = Path(
            file.filename
        ).name

        file_extension = Path(
            filename
        ).suffix.lower()

        # --------------------------------
        # 2. Validate file type
        # --------------------------------

        if file_extension not in SUPPORTED_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only .txt, .pdf, and .docx "
                    "files are supported"
                )
            )

        # --------------------------------
        # 3. Check for duplicate
        # --------------------------------

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id
                    FROM documents
                    WHERE filename = %s;
                    """,
                    (filename,)
                )

                existing_document = (
                    cur.fetchone()
                )

        if existing_document:

            raise HTTPException(
                status_code=409,
                detail=(
                    f"Document '{filename}' "
                    "already exists"
                )
            )

        # --------------------------------
        # 4. Read uploaded file
        # --------------------------------

        content = await file.read()

        if not content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        # --------------------------------
        # 5. Save file
        # --------------------------------

        file_path = (
            DOCUMENTS_DIR / filename
        )

        with open(
            file_path,
            "wb"
        ) as document:

            document.write(content)

        # --------------------------------
        # 6. Ingest document
        # --------------------------------

        ingestion_result = ingest_document(
            str(file_path)
        )

        # --------------------------------
        # 7. Return result
        # --------------------------------

        return {
            "message": (
                "Document uploaded and "
                "indexed successfully"
            ),
            "filename": filename,
            "file_type": file_extension,
            "title": ingestion_result.get(
                "title"
            ),
            "characters": ingestion_result.get(
                "characters"
            ),
            "chunks": ingestion_result.get(
                "chunks"
            ),
            "document_id": ingestion_result.get(
                "document_id"
            )
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# List Documents
# --------------------------------

@app.get("/documents")
def list_documents():

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        d.id,
                        d.filename,
                        d.file_type,
                        d.title,
                        d.created_at,
                        COUNT(dc.id) AS chunk_count
                    FROM documents d

                    LEFT JOIN document_chunks dc
                        ON d.id = dc.document_id

                    GROUP BY
                        d.id,
                        d.filename,
                        d.file_type,
                        d.title,
                        d.created_at

                    ORDER BY
                        d.created_at DESC;
                    """
                )

                rows = cur.fetchall()

        documents = []

        for row in rows:

            (
                document_id,
                filename,
                file_type,
                title,
                created_at,
                chunk_count
            ) = row

            documents.append(
                {
                    "id": document_id,
                    "filename": filename,
                    "file_type": file_type,
                    "title": title,
                    "created_at": created_at,
                    "chunks": chunk_count
                }
            )

        return {
            "documents": documents,
            "count": len(documents)
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# Get Document
# --------------------------------

@app.get("/documents/{document_id}")
def get_document(document_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                # -----------------------------
                # Get document
                # -----------------------------

                cur.execute(
                    """
                    SELECT
                        id,
                        filename,
                        file_type,
                        title,
                        content,
                        created_at
                    FROM documents
                    WHERE id = %s;
                    """,
                    (document_id,)
                )

                document = cur.fetchone()

                if not document:

                    raise HTTPException(
                        status_code=404,
                        detail="Document not found"
                    )

                # -----------------------------
                # Get chunks
                # -----------------------------

                cur.execute(
                    """
                    SELECT
                        id,
                        chunk_index,
                        content
                    FROM document_chunks
                    WHERE document_id = %s
                    ORDER BY chunk_index;
                    """,
                    (document_id,)
                )

                chunks = cur.fetchall()

        (
            document_id,
            filename,
            file_type,
            title,
            content,
            created_at
        ) = document

        return {
            "id": document_id,
            "filename": filename,
            "file_type": file_type,
            "title": title,
            "content": content,
            "created_at": created_at,
            "chunks": [
                {
                    "id": chunk[0],
                    "chunk_index": chunk[1],
                    "content": chunk[2]
                }
                for chunk in chunks
            ]
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# Delete Document
# --------------------------------

@app.delete("/documents/{document_id}")
def delete_document(document_id: int):

    try:

        with get_connection() as conn:

            with conn.cursor() as cur:

                # -----------------------------
                # Check document exists
                # -----------------------------

                cur.execute(
                    """
                    SELECT
                        id,
                        filename
                    FROM documents
                    WHERE id = %s;
                    """,
                    (document_id,)
                )

                document = cur.fetchone()

                if not document:

                    raise HTTPException(
                        status_code=404,
                        detail="Document not found"
                    )

                filename = document[1]

                # -----------------------------
                # Delete document
                # -----------------------------

                cur.execute(
                    """
                    DELETE FROM documents
                    WHERE id = %s;
                    """,
                    (document_id,)
                )

                deleted_chunks = cur.rowcount

            conn.commit()

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "filename": filename
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )