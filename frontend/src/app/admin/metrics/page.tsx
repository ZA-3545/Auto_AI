"use client";

import { useCallback, useEffect, useState } from "react";
import { BarChart3, Loader2, RefreshCw } from "lucide-react";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  fetchAdminMetrics,
  type AdminMetricsResponse,
  type MetricCard,
} from "@/lib/api";

function statusStyles(status: MetricCard["status"]) {
  switch (status) {
    case "computed":
      return "bg-emerald-50 text-emerald-900 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-100 dark:border-emerald-900";
    case "manual":
      return "bg-sky-50 text-sky-900 border-sky-200 dark:bg-sky-950/40 dark:text-sky-100 dark:border-sky-900";
    default:
      return "bg-muted/60 text-muted-foreground border-border";
  }
}

function statusLabel(status: MetricCard["status"]) {
  switch (status) {
    case "computed":
      return "Computed";
    case "manual":
      return "Manual / test suite";
    default:
      return "Not yet available";
  }
}

function MetricCardView({ metric }: { metric: MetricCard }) {
  return (
    <article className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-sm font-semibold leading-snug">{metric.label}</h3>
        <span
          className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${statusStyles(metric.status)}`}
        >
          {statusLabel(metric.status)}
        </span>
      </div>
      {metric.value != null ? (
        <p className="text-2xl font-semibold tabular-nums tracking-tight">
          {metric.value}
          {metric.unit ? (
            <span className="ml-1 text-sm font-normal text-muted-foreground">
              {metric.unit}
            </span>
          ) : null}
        </p>
      ) : (
        <p className="text-sm text-muted-foreground">—</p>
      )}
      {metric.detail ? (
        <p className="mt-2 text-xs text-muted-foreground">{metric.detail}</p>
      ) : null}
      {metric.note ? (
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground/90">
          {metric.note}
        </p>
      ) : null}
    </article>
  );
}

export default function AdminMetricsPage() {
  const [data, setData] = useState<AdminMetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchAdminMetrics());
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Failed to load metrics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const computed = data?.metrics.filter((m) => m.status === "computed") ?? [];
  const manual = data?.metrics.filter((m) => m.status === "manual") ?? [];
  const unavailable =
    data?.metrics.filter((m) => m.status === "not_available") ?? [];

  return (
    <div className="flex min-h-full flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <div className="mb-6 space-y-3">
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
            Internal · Evaluation metrics
          </p>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Metrics dashboard
              </h1>
              <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
                PLANNING.md Section K.1 — read-only PoC reporting over in-process
                counters and DB tables. Session counters reset when the backend
                restarts.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              disabled={loading}
              onClick={() => void load()}
            >
              {loading ? (
                <Loader2 className="animate-spin" data-icon="inline-start" />
              ) : (
                <RefreshCw data-icon="inline-start" />
              )}
              Refresh
            </Button>
          </div>
          <p className="rounded-lg border border-amber-200/80 bg-amber-50/80 px-3 py-2 text-xs leading-relaxed text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-100">
            Internal use only — no authentication yet (Phase 8). Add access control
            before any public deployment. Metrics marked &quot;Not yet available&quot;
            are not fabricated per Section H.
          </p>
        </div>

        {error ? (
          <p className="mb-6 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {loading && !data ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading metrics…
          </p>
        ) : null}

        {data ? (
          <div className="space-y-10">
            <p className="text-xs text-muted-foreground">
              Generated {new Date(data.generated_at).toLocaleString()} ·{" "}
              {data.disclaimer}
            </p>

            <section className="space-y-3">
              <h2 className="flex items-center gap-2 text-lg font-semibold">
                <BarChart3 className="size-5" />
                Computed ({computed.length})
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {computed.map((m) => (
                  <MetricCardView key={m.id} metric={m} />
                ))}
              </div>
            </section>

            {manual.length > 0 ? (
              <section className="space-y-3">
                <h2 className="text-lg font-semibold">
                  Manual / test suite ({manual.length})
                </h2>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {manual.map((m) => (
                    <MetricCardView key={m.id} metric={m} />
                  ))}
                </div>
              </section>
            ) : null}

            <section className="space-y-3">
              <h2 className="text-lg font-semibold">
                Not yet available ({unavailable.length})
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {unavailable.map((m) => (
                  <MetricCardView key={m.id} metric={m} />
                ))}
              </div>
            </section>

            {data.endpoint_latency.length > 0 ? (
              <section className="space-y-3">
                <h2 className="text-lg font-semibold">Endpoint latency</h2>
                <div className="overflow-x-auto rounded-xl border border-border">
                  <table className="w-full min-w-[520px] text-left text-sm">
                    <thead className="border-b border-border bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
                      <tr>
                        <th className="px-4 py-2 font-medium">Path</th>
                        <th className="px-4 py-2 font-medium">Requests</th>
                        <th className="px-4 py-2 font-medium">Errors</th>
                        <th className="px-4 py-2 font-medium">Avg ms</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.endpoint_latency.map((row) => (
                        <tr
                          key={row.path}
                          className="border-b border-border/60 last:border-0"
                        >
                          <td className="px-4 py-2 font-mono text-xs">
                            {row.path}
                          </td>
                          <td className="px-4 py-2 tabular-nums">
                            {row.request_count}
                          </td>
                          <td className="px-4 py-2 tabular-nums">
                            {row.error_count}
                          </td>
                          <td className="px-4 py-2 tabular-nums">
                            {row.avg_latency_ms ?? "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ) : null}

            {Object.keys(data.llm_by_operation).length > 0 ? (
              <section className="space-y-3">
                <h2 className="text-lg font-semibold">LLM calls by operation</h2>
                <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {Object.entries(data.llm_by_operation).map(([op, count]) => (
                    <li
                      key={op}
                      className="rounded-lg border border-border/80 bg-muted/20 px-3 py-2 text-sm"
                    >
                      <span className="font-mono text-xs">{op}</span>
                      <span className="ml-2 tabular-nums font-medium">{count}</span>
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
