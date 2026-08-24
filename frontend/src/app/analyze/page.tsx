"use client";

import { FormEvent, useState } from "react";
import { ClipboardList, Loader2, SearchCheck } from "lucide-react";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  analyzeListing,
  type AnalyzeListingResponse,
  type DataReliability,
  type LabeledClaim,
} from "@/lib/api";
import { formatPkr } from "@/lib/format";

const SAMPLE_LISTING = `2019 Toyota Corolla Altis, 75,000 km, Lahore, PKR 42 lakh.
Automatic, petrol. Single owner claimed. Accident free, original paint.
Urgent sale — leaving country.`;

function ReliabilityBadge({ reliability }: { reliability: DataReliability }) {
  const styles: Record<DataReliability, string> = {
    fact: "bg-emerald-50 text-emerald-900 border-emerald-200",
    inference: "bg-amber-50 text-amber-950 border-amber-200",
    unknown: "bg-slate-100 text-slate-800 border-slate-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${styles[reliability]}`}
    >
      {reliability}
    </span>
  );
}

function ClaimList({
  title,
  items,
  empty,
}: {
  title: string;
  items: LabeledClaim[];
  empty: string;
}) {
  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold tracking-tight">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li
              key={`${item.category}-${item.text.slice(0, 40)}`}
              className="flex gap-3 border-b border-border/60 pb-2 last:border-0"
            >
              <ReliabilityBadge reliability={item.reliability} />
              <p className="text-sm leading-relaxed text-foreground/90">
                {item.text}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-[7.5rem_1fr] gap-2 text-sm sm:grid-cols-[9rem_1fr]">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium text-foreground">{value}</dd>
    </div>
  );
}

export default function AnalyzeListingPage() {
  const [text, setText] = useState(SAMPLE_LISTING);
  const [result, setResult] = useState<AnalyzeListingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await analyzeListing(text.trim());
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const extracted = result?.extracted;
  const price = result?.price_assessment;

  return (
    <div className="flex min-h-full flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6">
        <div className="mb-8 space-y-2">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
            Listing analyzer
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Analyze this listing
          </h1>
          <p className="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Paste a seller ad. We extract structured details, compare the asking
            price to our reference dataset, and surface labeled caveats — never
            inventing accident-free or mechanical certainty.
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-3">
          <label className="block space-y-2">
            <span className="text-sm font-medium">Listing text</span>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={7}
              className="w-full resize-y rounded-lg border border-border bg-background px-3 py-2.5 text-sm leading-relaxed shadow-sm outline-none ring-ring/30 placeholder:text-muted-foreground focus-visible:ring-3"
              placeholder="e.g. 2019 Corolla Altis, 75,000 km, Lahore, PKR 42 lakh"
              required
            />
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <Button type="submit" disabled={loading || !text.trim()} size="lg">
              {loading ? (
                <>
                  <Loader2 className="animate-spin" data-icon="inline-start" />
                  Analyzing…
                </>
              ) : (
                <>
                  <SearchCheck data-icon="inline-start" />
                  Analyze listing
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="lg"
              onClick={() => setText(SAMPLE_LISTING)}
            >
              <ClipboardList data-icon="inline-start" />
              Load sample
            </Button>
          </div>
        </form>

        {error ? (
          <p className="mt-6 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {result && extracted && price ? (
          <div className="mt-10 space-y-8 border-t border-border pt-8">
            {result.advisor_summary ? (
              <section className="space-y-2">
                <h2 className="text-lg font-semibold tracking-tight">Summary</h2>
                <p className="text-sm leading-relaxed text-foreground/90">
                  {result.advisor_summary}
                </p>
                <p className="text-xs text-muted-foreground">
                  Summary source: {result.advisor_summary_source} · {result.provider}/
                  {result.model}
                </p>
              </section>
            ) : null}

            <section className="space-y-3">
              <h2 className="text-lg font-semibold tracking-tight">
                Extracted details
              </h2>
              <dl className="space-y-2 rounded-lg border border-border/80 bg-muted/20 p-4">
                <DetailRow
                  label="Vehicle"
                  value={
                    [extracted.make, extracted.model, extracted.variant]
                      .filter(Boolean)
                      .join(" ") || "—"
                  }
                />
                <DetailRow
                  label="Year"
                  value={extracted.year != null ? String(extracted.year) : "—"}
                />
                <DetailRow
                  label="Asking price"
                  value={
                    extracted.asking_price != null
                      ? formatPkr(extracted.asking_price)
                      : "—"
                  }
                />
                <DetailRow
                  label="Mileage"
                  value={
                    extracted.mileage_km != null
                      ? `${extracted.mileage_km.toLocaleString()} km`
                      : "—"
                  }
                />
                <DetailRow label="Location" value={extracted.location ?? "—"} />
                <DetailRow
                  label="Transmission"
                  value={extracted.transmission ?? "—"}
                />
                <DetailRow label="Fuel" value={extracted.fuel_type ?? "—"} />
                <DetailRow
                  label="Engine"
                  value={
                    extracted.engine_capacity != null
                      ? `${extracted.engine_capacity} cc`
                      : "—"
                  }
                />
              </dl>
            </section>

            <section className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold tracking-tight">
                  Price assessment
                </h2>
                <ReliabilityBadge reliability={price.reliability} />
                <span className="rounded border border-border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  {price.relative.replace("_", " ")}
                </span>
              </div>
              <p className="text-sm leading-relaxed">{price.summary}</p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {price.dataset_disclaimer}
              </p>
              {price.reference_count > 0 ? (
                <p className="text-xs text-muted-foreground">
                  Reference comps: {price.reference_count}
                  {price.reference_median != null
                    ? ` · median ${formatPkr(price.reference_median)}`
                    : ""}
                  {price.reference_min != null && price.reference_max != null
                    ? ` · range ${formatPkr(price.reference_min)}–${formatPkr(price.reference_max)}`
                    : ""}
                </p>
              ) : null}
            </section>

            <ClaimList
              title="Red flags"
              items={result.red_flags}
              empty="No heuristic red flags from the pasted text."
            />
            <ClaimList
              title="Missing information"
              items={result.missing_information}
              empty="No obvious gaps detected."
            />
            <ClaimList
              title="Notes"
              items={result.notes}
              empty="No additional notes."
            />

            <section className="space-y-3">
              <h3 className="text-sm font-semibold tracking-tight">
                Questions to ask the seller
              </h3>
              <ol className="list-decimal space-y-1.5 pl-5 text-sm leading-relaxed">
                {result.seller_questions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ol>
            </section>
          </div>
        ) : null}
      </main>
      <SiteFooter />
    </div>
  );
}
