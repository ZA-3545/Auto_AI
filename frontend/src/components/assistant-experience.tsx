"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { GitCompareArrows, RotateCcw, Search } from "lucide-react";

import { ComparisonView } from "@/components/comparison-view";
import { RecommendationCard } from "@/components/recommendation-card";
import { RequirementSummary } from "@/components/requirement-summary";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  compareVehicles,
  extractRequirements,
  getStoredConversationId,
  recommendVehicles,
  resetConversation,
  type CompareResponse,
  type ExtractedRequirements,
  type ExtractResponse,
  type RecommendResponse,
} from "@/lib/api";
import { QUICK_PROMPTS } from "@/lib/format";

const MAX_COMPARE = 4;

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

type Props = {
  initialPrompt?: string;
};

export function AssistantExperience({ initialPrompt = "" }: Props) {
  const [message, setMessage] = useState(initialPrompt);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [extracted, setExtracted] = useState<ExtractResponse | null>(null);
  const [sessionRequirements, setSessionRequirements] =
    useState<ExtractedRequirements>(EMPTY_REQUIREMENTS);
  const [recommendations, setRecommendations] =
    useState<RecommendResponse | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const resultsRef = useRef<HTMLElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    setConversationId(getStoredConversationId());
  }, []);

  useEffect(() => {
    if (initialPrompt) {
      setMessage(initialPrompt);
    }
  }, [initialPrompt]);

  function applyQuickPrompt(prompt: string) {
    setMessage(prompt);
    inputRef.current?.focus();
    // Scroll to composer on mobile
    inputRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function toggleSelect(id: number) {
    setComparison(null);
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_COMPARE) return prev;
      return [...prev, id];
    });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setRecommendations(null);
    setSelectedIds([]);
    setComparison(null);

    try {
      const extractResult = await extractRequirements(message, {
        conversationId,
      });
      setExtracted(extractResult);
      setSessionRequirements(extractResult.requirements);
      if (extractResult.conversation_id) {
        setConversationId(extractResult.conversation_id);
      }

      const req = extractResult.requirements;
      if (req.needs_clarification) {
        setError(
          req.clarification_question ??
            "Please clarify that detail so we can search accurately.",
        );
        return;
      }

      const recResult = await recommendVehicles(req);
      setRecommendations(recResult);
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
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
      setExtracted(null);
      setRecommendations(null);
      setSelectedIds([]);
      setComparison(null);
      setMessage("");
      inputRef.current?.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset session");
    } finally {
      setLoading(false);
    }
  }

  async function onCompare() {
    if (!extracted || selectedIds.length < 2) return;
    setComparing(true);
    setError(null);
    try {
      const result = await compareVehicles(
        selectedIds,
        extracted.requirements,
        true,
      );
      setComparison(result);
      requestAnimationFrame(() => {
        document
          .getElementById("comparison")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (err) {
      setComparison(null);
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setComparing(false);
    }
  }

  return (
    <div className="flex min-h-full flex-1 flex-col bg-[linear-gradient(180deg,oklch(0.97_0.01_85)_0%,oklch(1_0_0)_28%)] dark:bg-none">
      <SiteHeader />

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-10 px-4 py-8 sm:px-6 sm:py-12">
        {/* Hero */}
        <section className="space-y-5 text-center sm:space-y-6 sm:pt-4">
          <p className="text-sm font-medium tracking-wide text-muted-foreground">
            AutoAI
          </p>
          <h1 className="mx-auto max-w-3xl text-3xl font-semibold tracking-tight text-balance sm:text-4xl md:text-5xl">
            Find the right car with AI
          </h1>
          <p className="mx-auto max-w-2xl text-base text-muted-foreground text-pretty sm:text-lg">
            Tell us your budget, needs and priorities. Our AI will help you
            discover and compare the best options.
          </p>
          <p className="mx-auto max-w-2xl text-xs text-muted-foreground sm:text-sm">
            Independent proof of concept — not affiliated with or endorsed by
            PakWheels.
          </p>
        </section>

        {/* Composer */}
        <section className="mx-auto w-full max-w-3xl space-y-4 rounded-2xl border border-border bg-card/90 p-4 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-medium">Describe what you need</h2>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              disabled={loading}
              onClick={() => void onStartNewSearch()}
            >
              <RotateCcw data-icon="inline-start" />
              Start new search
            </Button>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <textarea
              ref={inputRef}
              className="min-h-28 w-full resize-y rounded-xl border border-input bg-background px-3 py-3 text-sm sm:text-base"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="e.g. Family car under 30 lakh in Lahore, preferably automatic"
            />

            <div className="flex flex-wrap gap-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="rounded-full border border-border bg-background px-3 py-1.5 text-left text-xs text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground sm:text-sm"
                  onClick={() => applyQuickPrompt(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>

            <Button
              type="submit"
              size="lg"
              className="w-full sm:w-auto"
              disabled={loading || !message.trim()}
            >
              <Search data-icon="inline-start" />
              {loading ? "Searching…" : "Find matching cars"}
            </Button>
          </form>

          {error && (
            <p className="rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
        </section>

        <RequirementSummary requirements={sessionRequirements} />

        {recommendations && (
          <section ref={resultsRef} className="space-y-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold tracking-tight">
                  Matching options
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {recommendations.total_candidates} in catalog · showing{" "}
                  {recommendations.items.length}. Select 2–{MAX_COMPARE} to
                  compare ({selectedIds.length} selected).
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                disabled={selectedIds.length < 2 || comparing}
                onClick={() => void onCompare()}
                className="w-full sm:w-auto"
              >
                <GitCompareArrows data-icon="inline-start" />
                {comparing ? "Comparing…" : "Compare selected"}
              </Button>
            </div>

            {recommendations.items.length === 0 ? (
              <p className="rounded-xl border border-dashed border-border p-6 text-sm text-muted-foreground">
                No vehicles in the demo catalog matched these filters. Try a
                wider budget or fewer constraints.
              </p>
            ) : (
              <ul className="space-y-4">
                {recommendations.items.map((item, index) => (
                  <li key={item.vehicle.id}>
                    <RecommendationCard
                      item={item}
                      rank={index + 1}
                      selected={selectedIds.includes(item.vehicle.id)}
                      onToggleSelect={() => toggleSelect(item.vehicle.id)}
                      selectDisabled={selectedIds.length >= MAX_COMPARE}
                    />
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {comparison && <ComparisonView comparison={comparison} />}

        <p className="text-center text-xs text-muted-foreground">
          Scores are deterministic matches against your stated needs — not sales
          rankings.{" "}
          <Link href="/vehicles" className="underline-offset-2 hover:underline">
            Browse the demo catalog
          </Link>
        </p>
      </main>

      <SiteFooter />
    </div>
  );
}
