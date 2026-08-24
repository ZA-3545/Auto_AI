"use client";

import { FormEvent, useState } from "react";
import { BookOpen, Loader2 } from "lucide-react";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  askKnowledgeQuestion,
  type KnowledgeAskResponse,
} from "@/lib/api";

const SAMPLE_QUESTIONS = [
  "What does CVT mean?",
  "What should I check before buying a used car?",
  "What does resale value depend on?",
  "What does engine capacity mean?",
] as const;

export default function KnowledgeAskPage() {
  const [question, setQuestion] = useState(SAMPLE_QUESTIONS[0]);
  const [result, setResult] = useState<KnowledgeAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await askKnowledgeQuestion(question.trim());
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-full flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6">
        <div className="mb-6 space-y-2">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
            Knowledge base
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Ask a question
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            General automotive education from AutoAI&apos;s sample knowledge base
            (RAG). This is separate from Find a car — it does not search inventory
            or invent listings.
          </p>
          <p className="rounded-lg border border-border/80 bg-muted/40 px-3 py-2 text-xs leading-relaxed text-muted-foreground">
            General educational information only — not professional mechanical or
            financial advice. Independent proof of concept — not affiliated with
            PakWheels.
          </p>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          {SAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => setQuestion(q)}
              className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
            >
              {q}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="space-y-3">
          <label className="block space-y-2">
            <span className="text-sm font-medium">Your question</span>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              className="w-full resize-y rounded-lg border border-border bg-background px-3 py-2.5 text-sm leading-relaxed shadow-sm outline-none ring-ring/30 focus-visible:ring-3"
              placeholder="e.g. What does CVT mean?"
              required
            />
          </label>
          <Button type="submit" disabled={loading || !question.trim()} size="lg">
            {loading ? (
              <>
                <Loader2 className="animate-spin" data-icon="inline-start" />
                Searching knowledge…
              </>
            ) : (
              <>
                <BookOpen data-icon="inline-start" />
                Ask
              </>
            )}
          </Button>
        </form>

        {error ? (
          <p className="mt-6 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {result ? (
          <div className="mt-10 space-y-6 border-t border-border pt-8">
            <section className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold tracking-tight">Answer</h2>
                <span className="rounded border border-border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {result.grounded ? "grounded in knowledge base" : "insufficient retrieval"}
                </span>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
                {result.answer}
              </p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {result.disclaimer}
              </p>
              {result.provider ? (
                <p className="text-xs text-muted-foreground">
                  {result.provider}/{result.model}
                </p>
              ) : null}
            </section>

            {result.chunks.length > 0 ? (
              <section className="space-y-3">
                <h3 className="text-sm font-semibold tracking-tight">
                  Retrieved sources
                </h3>
                <ul className="space-y-3">
                  {result.chunks.map((c) => (
                    <li
                      key={c.id}
                      className="rounded-lg border border-border/80 bg-muted/20 p-3"
                    >
                      <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
                        <p className="text-sm font-medium">{c.title}</p>
                        <span className="text-[11px] text-muted-foreground">
                          similarity {(c.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed text-muted-foreground">
                        {c.content}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
          </div>
        ) : null}
      </main>
      <SiteFooter />
    </div>
  );
}
