# Enterprise Knowledge Intelligence Platform

An enterprise-grade Retrieval-Augmented Generation (RAG) platform that allows users to upload organizational documents and ask natural-language questions over the knowledge base.

The system combines semantic vector search, PostgreSQL full-text search, query rewriting, reranking, conversation-aware retrieval, and LLM generation to produce grounded answers with source references.

---

## 🚀 Features

- 📄 Upload PDF, DOCX, and TXT documents
- ✂️ Sentence-aware document chunking
- 🧠 Local text embeddings using Sentence Transformers
- 🔎 Hybrid retrieval using:
  - Vector similarity search
  - PostgreSQL full-text search
- 🎯 Retrieval score thresholding and abstention
- 🔄 Query rewriting for improved retrieval
- 💬 Conversation-aware follow-up questions
- 📊 Lightweight reranking of retrieved chunks
- 🤖 LLM-powered answer generation using Groq
- 📚 Source references for generated answers
- 🗂️ Document listing and deletion
- 🐳 Fully Dockerized development environment
- 🗄️ PostgreSQL with pgvector
- ⚡ FastAPI backend
- ⚛️ Next.js frontend

---

## 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      Next.js UI      │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │ Query        │  │ Hybrid       │  │ Reranking    │
          │ Rewriting    │  │ Retrieval    │  │              │
          └──────────────┘  └──────┬───────┘  └──────┬───────┘
                                   │                 │
                                   ▼                 │
                         ┌──────────────────────┐    │
                         │ PostgreSQL + pgvector│◄───┘
                         │                      │
                         │ Vector Search        │
                         │ Full-Text Search     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Groq LLM           │
                         │   Answer Generation  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Answer + Sources     │
                         └──────────────────────┘
```

---

## 🔄 RAG Pipeline

```text
User Question
      │
      ▼
Conversation Rewriting
      │
      ▼
Query Rewriting
      │
      ▼
Hybrid Retrieval
      │
      ├── Vector Similarity Search
      │
      └── PostgreSQL Full-Text Search
      │
      ▼
Retrieval Threshold / Abstention
      │
      ▼
Reranking
      │
      ▼
Top Relevant Chunks
      │
      ▼
Context Construction
      │
      ▼
Groq LLM
      │
      ▼
Grounded Answer + Sources
```

---

## 🧠 Retrieval Strategy

The platform uses hybrid retrieval instead of relying solely on vector search.

### Vector Search

Documents are embedded using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The model produces 384-dimensional embeddings that are stored in PostgreSQL using `pgvector`.

### Keyword Search

PostgreSQL full-text search is used alongside vector search. Document chunks are represented using PostgreSQL `tsvector` values for keyword matching.

### Hybrid Score

The current retrieval score combines both signals:

```text
Hybrid Score =
    0.70 × Vector Score
  + 0.30 × Keyword Score
```

---

## 🎯 Retrieval Evaluation

A small evaluation dataset was created to measure retrieval quality.

The dataset contains:

- 8 answerable questions
- 2 unanswerable questions

Current evaluation results:

| Metric | Result |
|---|---:|
| Recall@1 | 100% |
| Recall@3 | 100% |
| Correct Rejection Rate | 100% |
| Total Questions | 10 |
| Answerable Questions | 8 |
| Unanswerable Questions | 2 |

The evaluation also includes an abstention threshold to prevent the system from attempting to answer questions when the retrieved evidence is insufficient.

---

## 💬 Conversation-Aware RAG

The system supports follow-up questions.

Example:

```text
User:
How many days per week can employees work remotely?

Assistant:
Employees may work remotely up to three days per week.

User:
Who approves it?
```

The conversation rewriter converts the follow-up into a standalone retrieval query, allowing the retrieval system to resolve references such as:

```text
it
they
them
this
that
the company
the policy
```

---

## 📄 Document Processing

Supported formats:

```text
.txt
.pdf
.docx
```

The ingestion pipeline performs:

```text
Document
   ↓
Text Extraction
   ↓
Sentence Splitting
   ↓
Chunking
   ↓
Embedding Generation
   ↓
Vector Storage
   ↓
Full-Text Indexing
```

Each document stores metadata including:

- Filename
- Title
- File type
- Creation timestamp

Each chunk stores:

- Document ID
- Chunk index
- Content
- Embedding
- Full-text search vector

---

## 🛠️ Tech Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend

- Python
- FastAPI
- Pydantic

### AI / RAG

- Groq
- OpenAI-compatible SDK
- Sentence Transformers
- `all-MiniLM-L6-v2`

### Database

- PostgreSQL
- pgvector
- PostgreSQL Full-Text Search

### Document Processing

- PyPDF
- python-docx

### Infrastructure

- Docker
- Docker Compose

---

## 📁 Project Structure

```text
enterprise-knowledge-intelligence-platform/
│
├── backend/
│   ├── evaluation/
│   ├── chunker.py
│   ├── conversation_rewriter.py
│   ├── database.py
│   ├── document_loader.py
│   ├── embeddings.py
│   ├── ingestion.py
│   ├── main.py
│   ├── query_rewriter.py
│   ├── rag.py
│   ├── reranker.py
│   ├── retriever.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── docker-compose.yml
├── init.sql
├── .gitignore
└── README.md
```

---

## ⚙️ Running Locally

### Prerequisites

Install:

- Docker Desktop
- Git

You do not need to install PostgreSQL locally when using Docker Compose.

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit your `.env` file.

---

## 🐳 Run with Docker

Build and start the complete application:

```bash
docker compose up --build
```

The application will start:

```text
Frontend:
http://localhost:3000

Backend:
http://localhost:8000

PostgreSQL:
localhost:5433
```

Check the backend health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

---

## 💻 Local Development

### Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## 🔌 API Endpoints

### Health

```http
GET /health
```

### RAG Query

```http
POST /rag
```

Example request:

```json
{
  "question": "What technical skills are present in the resume?",
  "conversation": []
}
```

### Upload Document

```http
POST /documents/upload
```

Accepts PDF, DOCX, and TXT files.

### List Documents

```http
GET /documents
```

### Get Document

```http
GET /documents/{id}
```

### Delete Document

```http
DELETE /documents/{id}
```

---

## 🔒 Grounded Generation

The LLM is instructed to answer using only the retrieved document context.

The generation layer follows these principles:

1. Do not use outside knowledge.
2. Do not invent information.
3. If the retrieved context does not contain the answer, state that the information is unavailable.
4. Prefer higher-ranked relevant sources.
5. Return source references alongside the answer.

---

## 📊 Example

After uploading a resume:

```text
User:
What technical skills are present in the resume?
```

The system retrieves relevant resume chunks and generates a grounded response containing categories such as:

```text
Languages:
Java, JavaScript, TypeScript, SQL

Frontend:
React.js, Next.js, HTML, CSS, Tailwind CSS

Backend:
Node.js, Express.js, REST APIs, Middleware, JWT Authentication

Databases:
PostgreSQL, MongoDB, Prisma ORM

Cloud / DevOps:
AWS EC2, AWS RDS, AWS S3, AWS IAM, Docker, Nginx, Git, GitHub, Bash
```

The response also includes the document chunks used as sources.

---

## 🚧 Future Improvements

- Cross-encoder reranking
- Streaming LLM responses
- Authentication and role-based access control
- Multi-user workspaces
- Document-level permissions
- Conversation persistence
- Advanced evaluation datasets
- Retrieval latency monitoring
- Answer faithfulness evaluation
- Cloud deployment
- CI/CD pipeline
- Production observability

---

## 👨‍💻 Author

**Krish Gupta**

Integrated M.Tech Computer Science  
VIT-AP University

---

## ⭐ Project Highlights

This project demonstrates practical implementation of:

- Retrieval-Augmented Generation
- Semantic search
- Hybrid information retrieval
- Vector databases
- PostgreSQL + pgvector
- LLM application development
- Document ingestion pipelines
- Conversational retrieval
- FastAPI
- Next.js
- Dockerized full-stack development
