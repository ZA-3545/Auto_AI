"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { API_URL, fetchHealth, type HealthResponse } from "@/lib/api";

type Status = "loading" | "ok" | "error";

export function HealthCheck() {
  const [status, setStatus] = useState<Status>("loading");
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const check = useCallback(async () => {
    setStatus("loading");
    setError(null);

    try {
      const result = await fetchHealth();
      setData(result);
      setStatus("ok");
    } catch (err) {
      setData(null);
      setStatus("error");
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return (
    <section className="w-full max-w-lg space-y-4 rounded-xl border border-border bg-card p-6 text-card-foreground shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">API health</h2>
          <p className="text-sm text-muted-foreground">{API_URL}/health</p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => void check()}
          disabled={status === "loading"}
        >
          <RefreshCw
            data-icon="inline-start"
            className={status === "loading" ? "animate-spin" : undefined}
          />
          Recheck
        </Button>
      </div>

      {status === "loading" && (
        <p className="text-sm text-muted-foreground">Checking backend…</p>
      )}

      {status === "ok" && data && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Status</dt>
          <dd className="font-medium text-emerald-700 dark:text-emerald-400">
            {data.status}
          </dd>
          <dt className="text-muted-foreground">Service</dt>
          <dd>{data.service}</dd>
          <dt className="text-muted-foreground">Version</dt>
          <dd>{data.version}</dd>
          <dt className="text-muted-foreground">Environment</dt>
          <dd>{data.environment}</dd>
          <dt className="text-muted-foreground">Timestamp</dt>
          <dd className="font-mono text-xs">{data.timestamp}</dd>
        </dl>
      )}

      {status === "error" && (
        <div className="space-y-2 text-sm">
          <p className="font-medium text-destructive">Backend unreachable</p>
          <p className="text-muted-foreground">{error}</p>
          <p className="text-muted-foreground">
            Start the API with{" "}
            <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
              uvicorn app.main:app --reload
            </code>{" "}
            from the <code className="font-mono text-xs">backend</code> folder.
          </p>
        </div>
      )}
    </section>
  );
}
