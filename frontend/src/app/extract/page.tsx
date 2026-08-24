"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { RotateCcw, Search } from "lucide-react";

import { RequirementSummary } from "@/components/requirement-summary";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  extractRequirements,
  getStoredConversationId,
  resetConversation,
  type ExtractedRequirements,
  type ExtractResponse,
} from "@/lib/api";
import { QUICK_PROMPTS } from "@/lib/format";

const EMPTY_REQUIREMENTS: ExtractedRequirements = {
  budget_min: null,
  budget_max: null,
  city: null,
  condition: null,
  transmission: null,
  body_type: null,
  purpose: null,
  fuel_priority: null,
  resale_priority: null,
  needs_clarification: false,
  clarification_question: null,
};

export default function ExtractPage() {
  const [message, setMessage] = useState<string>(QUICK_PROMPTS[0]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [sessionRequirements, setSessionRequirements] =
    useState<ExtractedRequirements>(EMPTY_REQUIREMENTS);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setConversationId(getStoredConversationId());
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await extractRequirements(message, { conversationId });
      setResult(data);
      setSessionRequirements(data.requirements);
      if (data.conversation_id) setConversationId(data.conversation_id);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Extraction failed");
    } finally {
      setLoading(false);
    }
  }

  async function onStartNewSearch() {
    setLoading(true);
    setError(null);
    try {
      if (conversationId) {
        const reset = await resetConversation(conversationId);
        setSessionRequirements(reset.requirements);
      } else {
        setSessionRequirements(EMPTY_REQUIREMENTS);
      }
      setResult(null);
      setMessage("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <SiteHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            <Link href="/" className="underline-offset-4 hover:underline">
              AutoAI
            </Link>{" "}
            · Requirements only
          </p>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Refine what you need
          </h1>
          <p className="text-sm text-muted-foreground">
            Multi-turn memory keeps prior details. For full results, use{" "}
            <Link href="/" className="underline-offset-2 hover:underline">
              Find a car
            </Link>
            .
          </p>
        </div>

        <div className="flex justify-end">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={loading}
            onClick={() => void onStartNewSearch()}
          >
            <RotateCcw data-icon="inline-start" />
            Start new search
          </Button>
        </div>

        <RequirementSummary requirements={sessionRequirements} />

        <form onSubmit={onSubmit} className="space-y-4 rounded-xl border border-border p-4">
          <textarea
            className="min-h-28 w-full rounded-xl border border-input bg-background px-3 py-3 text-sm"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add another detail…"
          />
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
                onClick={() => setMessage(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
          <Button type="submit" disabled={loading || !message.trim()}>
            <Search data-icon="inline-start" />
            {loading ? "Updating…" : "Update requirements"}
          </Button>
        </form>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {result?.turn_requirements && (
          <RequirementSummary
            requirements={result.turn_requirements}
            title="Added this turn"
            emptyHint="No new filters detected in that message."
          />
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
