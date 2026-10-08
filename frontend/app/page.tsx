"use client";

import { FormEvent, useEffect, useState } from "react";

type Source = {
  document_id: number;
  title: string | null;
  document: string;
  file_type: string | null;
  chunk_id: number;
  chunk_index: number;
  vector_score: number;
  keyword_score: number;
  hybrid_score: number;
  content: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

type Document = {
  id: number;
  filename: string;
  title: string | null;
  file_type: string | null;
  created_at?: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");

  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadDocuments() {
    try {
      const response = await fetch(`${API_URL}/documents`);

      if (!response.ok) {
        throw new Error("Failed to load documents");
      }

      const data = await response.json();

      // Backend may return either an array directly
      // or an object containing documents.
      if (Array.isArray(data)) {
        setDocuments(data);
      } else {
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleUpload(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);

        throw new Error(
          data?.detail || "Failed to upload document."
        );
      }

      await loadDocuments();
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to upload document."
      );
    } finally {
      setUploading(false);

      // Allow uploading the same file again.
      event.target.value = "";
    }
  }

  async function handleDelete(documentId: number) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this document?"
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(documentId);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/documents/${documentId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);

        throw new Error(
          data?.detail || "Failed to delete document."
        );
      }

      await loadDocuments();
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete document."
      );
    } finally {
      setDeletingId(null);
    }
  }

  async function sendMessage(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    setError("");
    setQuestion("");

    const updatedMessages: Message[] = [
      ...messages,
      {
        role: "user",
        content: trimmedQuestion,
      },
    ];

    setMessages(updatedMessages);
    setLoading(true);

    try {
      const conversation = updatedMessages
        .slice(0, -1)
        .map((message) => ({
          role: message.role,
          content: message.content,
        }));

      const response = await fetch(
        `${API_URL}/rag`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: trimmedQuestion,
            conversation,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to get response from the backend."
        );
      }

      const data = await response.json();

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        },
      ]);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the knowledge assistant."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="flex min-h-screen">
        {/* SIDEBAR */}
        <aside className="hidden w-80 border-r border-slate-800 bg-slate-900 p-6 lg:block">
          <div className="mb-10">
            <h1 className="text-xl font-semibold">
              Enterprise Knowledge
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              Intelligence Platform
            </p>
          </div>

          {/* Workspace */}
          <div>
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Workspace
            </p>

            <button className="w-full rounded-lg bg-slate-800 px-4 py-3 text-left text-sm">
              Knowledge Assistant
            </button>
          </div>

          {/* Documents */}
          <div className="mt-8">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Documents
              </p>

              <label className="cursor-pointer rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium transition hover:bg-blue-500">
                {uploading ? "Uploading..." : "Upload"}

                <input
                  type="file"
                  accept=".txt,.pdf,.docx"
                  className="hidden"
                  onChange={handleUpload}
                  disabled={uploading}
                />
              </label>
            </div>

            <div className="space-y-2">
              {documents.length === 0 ? (
                <p className="rounded-lg border border-dashed border-slate-800 p-4 text-xs text-slate-500">
                  No documents uploaded yet.
                </p>
              ) : (
                documents.map((document) => (
                  <div
                    key={document.id}
                    className="group rounded-lg border border-slate-800 bg-slate-950/50 p-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p
                          className="truncate text-sm font-medium text-slate-300"
                          title={document.title || document.filename}
                        >
                          {document.title || document.filename}
                        </p>

                        <p className="mt-1 truncate text-xs text-slate-500">
                          {document.filename}
                        </p>
                      </div>

                      <button
                        onClick={() =>
                          handleDelete(document.id)
                        }
                        disabled={deletingId === document.id}
                        className="shrink-0 text-xs text-slate-600 transition hover:text-red-400 disabled:opacity-50"
                        title="Delete document"
                      >
                        {deletingId === document.id
                          ? "..."
                          : "Delete"}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* System */}
          <div className="mt-8">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              System
            </p>

            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Backend connected
            </div>
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <section className="flex min-h-screen flex-1 flex-col">
          {/* HEADER */}
          <header className="border-b border-slate-800 bg-slate-950 px-6 py-5">
            <div className="mx-auto flex max-w-5xl items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">
                  Knowledge Assistant
                </h2>

                <p className="text-sm text-slate-400">
                  Ask questions about your organization's knowledge
                  base.
                </p>
              </div>

              <div className="hidden items-center gap-2 text-sm text-slate-400 sm:flex">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Online
              </div>
            </div>
          </header>

          {/* CHAT */}
          <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-6">
            <div className="mx-auto max-w-4xl space-y-8">
              {messages.length === 0 && (
                <div className="flex min-h-[55vh] items-center justify-center">
                  <div className="max-w-xl text-center">
                    <div className="mb-6 inline-flex rounded-2xl border border-slate-800 bg-slate-900 p-4">
                      <span className="text-2xl">✦</span>
                    </div>

                    <h3 className="text-3xl font-semibold">
                      Ask your knowledge base
                    </h3>

                    <p className="mt-3 text-slate-400">
                      Search company documents and get grounded
                      answers with source references.
                    </p>

                    <div className="mt-8 grid gap-3 text-left sm:grid-cols-2">
                      {[
                        "How many vacation days do employees get?",
                        "What are the security requirements?",
                        "How many days can employees work remotely?",
                        "Who approves remote work?",
                      ].map((example) => (
                        <button
                          key={example}
                          onClick={() => setQuestion(example)}
                          className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300 transition hover:border-slate-700 hover:bg-slate-800"
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={index}
                  className={
                    message.role === "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >
                  <div
                    className={
                      message.role === "user"
                        ? "max-w-2xl rounded-2xl bg-blue-600 px-5 py-4"
                        : "max-w-3xl"
                    }
                  >
                    {message.role === "assistant" && (
                      <div className="mb-2 text-xs font-medium uppercase tracking-wider text-slate-500">
                        Knowledge Assistant
                      </div>
                    )}

                    <div className="whitespace-pre-wrap leading-7 text-slate-200">
                      {message.content}
                    </div>

                    {message.sources &&
                      message.sources.length > 0 && (
                        <div className="mt-5">
                          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                            Sources
                          </p>

                          <div className="space-y-2">
                            {message.sources.map((source) => (
                              <div
                                key={source.chunk_id}
                                className="rounded-xl border border-slate-800 bg-slate-900 p-4"
                              >
                                <div className="flex items-center justify-between gap-4">
                                  <div>
                                    <p className="font-medium text-slate-200">
                                      {source.title ||
                                        source.document}
                                    </p>

                                    <p className="mt-1 text-xs text-slate-500">
                                      {source.document}
                                    </p>
                                  </div>

                                  <span className="rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-400">
                                    Chunk {source.chunk_index}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-3 text-sm text-slate-400">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-slate-500 [animation-delay:300ms]" />
                  </div>

                  Searching knowledge base...
                </div>
              )}

              {error && (
                <div className="rounded-xl border border-red-900 bg-red-950/40 p-4 text-sm text-red-300">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* INPUT */}
          <div className="border-t border-slate-800 bg-slate-950 p-4">
            <form
              onSubmit={sendMessage}
              className="mx-auto flex max-w-4xl gap-3"
            >
              <input
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                placeholder="Ask a question about your knowledge base..."
                disabled={loading}
                className="flex-1 rounded-xl border border-slate-800 bg-slate-900 px-5 py-4 text-sm text-white outline-none placeholder:text-slate-500 focus:border-slate-600"
              />

              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="rounded-xl bg-blue-600 px-6 py-4 text-sm font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </div>
        </section>
      </div>
    </main>
  );
}