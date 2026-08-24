"use client";

import { FormEvent, useState } from "react";
import { Lightbulb, Loader2 } from "lucide-react";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  askBuyingAdvice,
  type AdviceAskResponse,
} from "@/lib/api";

const SAMPLE_QUESTIONS = [
  "Should I buy a used car or new one on this budget?",
  "Is it better to buy from a dealer or private seller in Pakistan?",
  "What's the biggest mistake first-time car buyers make?",
  "What should I know about car financing in general?",
] as const;

export default function BuyingAdvicePage() {
  const [question, setQuestion] = useState(SAMPLE_QUESTIONS[0]);
  const [result, setResult] = useState<AdviceAskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await askBuyingAdvice(question.trim());
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
            Buying advice
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Ask for buying advice
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            General decision guidance for Pakistan&apos;s car market — used vs new,
            seller types, budgeting, and common mistakes. This is separate from{" "}
            <span className="font-medium text-foreground/80">Ask a question</span>,
            which covers automotive terminology and mechanics.
          </p>
          <p className="rounded-lg border border-border/80 bg-muted/40 px-3 py-2 text-xs leading-relaxed text-muted-foreground">
            Honest advisor, not a salesperson — balanced trade-offs, no push to
            buy. General educational guidance only — not individualized financial
            or legal advice. Independent proof of concept — not affiliated with
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
            <span className="text-sm font-medium">Your buying question</span>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              className="w-full resize-y rounded-lg border border-border bg-background px-3 py-2.5 text-sm leading-relaxed shadow-sm outline-none ring-ring/30 focus-visible:ring-3"
              placeholder="e.g. Should I buy from a dealer or private seller?"
              required
            />
          </label>
          <Button type="submit" disabled={loading || !question.trim()} size="lg">
            {loading ? (
              <>
                <Loader2 className="animate-spin" data-icon="inline-start" />
                Getting advice…
              </>
            ) : (
              <>
                <Lightbulb data-icon="inline-start" />
                Get advice
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
                <h2 className="text-lg font-semibold tracking-tight">Advice</h2>
                <span className="rounded border border-border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {result.grounded
                    ? "grounded in buying-advice knowledge"
                    : "insufficient retrieval"}
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
