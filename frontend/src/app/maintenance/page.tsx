"use client";

import { FormEvent, useState } from "react";
import { Loader2, Wrench } from "lucide-react";

import { MaintenanceChecklistView } from "@/components/maintenance-checklist-view";
import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  fetchMaintenanceChecklist,
  type MaintenanceResponse,
} from "@/lib/api";

const SAMPLE_DESCRIPTIONS = [
  "2018 Honda Civic with 80,000 km",
  "2022 Toyota Corolla, 25,000 km",
  "2015 Suzuki Alto, 100,000 km",
] as const;

export default function MaintenancePage() {
  const [description, setDescription] = useState(SAMPLE_DESCRIPTIONS[0]);
  const [result, setResult] = useState<MaintenanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await fetchMaintenanceChecklist({ description: description.trim() });
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
            Maintenance
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Maintenance checklist
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Describe a vehicle by make, model, year, and mileage. We extract
            structured details and build a general checklist from typical
            service intervals — not a substitute for a workshop inspection.
          </p>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          {SAMPLE_DESCRIPTIONS.map((sample) => (
            <button
              key={sample}
              type="button"
              onClick={() => setDescription(sample)}
              className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
            >
              {sample}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="space-y-3">
          <label className="block space-y-2">
            <span className="text-sm font-medium">Vehicle description</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full resize-y rounded-lg border border-border bg-background px-3 py-2.5 text-sm leading-relaxed shadow-sm outline-none ring-ring/30 focus-visible:ring-3"
              placeholder="e.g. 2018 Civic with 80,000 km"
              required
            />
          </label>
          <Button type="submit" disabled={loading || !description.trim()} size="lg">
            {loading ? (
              <>
                <Loader2 className="animate-spin" data-icon="inline-start" />
                Building checklist…
              </>
            ) : (
              <>
                <Wrench data-icon="inline-start" />
                Check maintenance
              </>
            )}
          </Button>
        </form>

        {error ? (
          <p className="mt-6 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {result ? <MaintenanceChecklistView result={result} /> : null}
      </main>
      <SiteFooter />
    </div>
  );
}
