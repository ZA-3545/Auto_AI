import Link from "next/link";

import type { CompareResponse } from "@/lib/api";
import { factorDisplayName } from "@/lib/format";

type Props = {
  comparison: CompareResponse;
};

export function ComparisonView({ comparison }: Props) {
  return (
    <section className="space-y-5" id="comparison">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Comparison</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Side-by-side factors from the catalog. Green cells mark the stronger
          option for that factor when one is clear.
        </p>
      </div>

      {comparison.narrative && (
        <div className="rounded-xl border border-border bg-muted/20 p-4 text-sm leading-relaxed">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Summary
          </p>
          <p className="whitespace-pre-wrap text-foreground/90">
            {comparison.narrative}
          </p>
        </div>
      )}

      <div className="rounded-xl border border-border p-4 sm:p-5">
        <h3 className="font-medium">Best overall for your priorities</h3>
        <p className="mt-2 text-sm leading-relaxed">
          <span className="font-semibold">
            {comparison.best_overall.vehicle_label}
          </span>
          <span className="text-muted-foreground">
            {" "}
            — {comparison.best_overall.reason}
          </span>
        </p>
        {comparison.best_for.length > 0 && (
          <ul className="mt-4 grid gap-2 sm:grid-cols-2">
            {comparison.best_for.map((item) => (
              <li
                key={item.category}
                className="rounded-lg border border-border bg-muted/20 px-3 py-2 text-sm"
              >
                <span className="block text-xs uppercase tracking-wide text-muted-foreground">
                  {factorDisplayName(item.category)}
                </span>
                <span className="font-medium">{item.vehicle_label}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Mobile: stacked cards per factor */}
      <div className="space-y-3 md:hidden">
        {comparison.factors.map((row) => {
          const byId = Object.fromEntries(
            row.values.map((v) => [v.vehicle_id, v]),
          );
          return (
            <div
              key={row.factor}
              className="rounded-xl border border-border p-3"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <h4 className="text-sm font-medium capitalize">
                  {factorDisplayName(row.factor)}
                </h4>
                <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {row.reliability}
                </span>
              </div>
              <ul className="space-y-2">
                {comparison.vehicles.map((v) => {
                  const cell = byId[v.id];
                  const isWinner = row.winner_vehicle_id === v.id;
                  return (
                    <li
                      key={v.id}
                      className={`rounded-md px-2 py-1.5 text-sm ${
                        isWinner
                          ? "bg-emerald-50 font-medium text-emerald-900 ring-1 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-100 dark:ring-emerald-800"
                          : "bg-muted/30"
                      }`}
                    >
                      <span className="block text-xs text-muted-foreground">
                        {v.make} {v.model}
                        {isWinner ? " · stronger" : ""}
                      </span>
                      {cell?.display ?? "—"}
                    </li>
                  );
                })}
              </ul>
              {row.note && (
                <p className="mt-2 text-xs text-muted-foreground">{row.note}</p>
              )}
            </div>
          );
        })}
      </div>

      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-xl border border-border md:block">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-border bg-muted/40">
            <tr>
              <th className="px-3 py-3 font-medium">Factor</th>
              {comparison.vehicles.map((v) => (
                <th key={v.id} className="px-3 py-3 font-medium">
                  <Link
                    href={`/vehicles/${v.id}`}
                    className="underline-offset-2 hover:underline"
                  >
                    {v.make} {v.model}
                  </Link>
                  <span className="mt-0.5 block text-xs font-normal text-muted-foreground">
                    {v.year} · details
                  </span>
                </th>
              ))}
              <th className="px-3 py-3 font-medium">Data</th>
            </tr>
          </thead>
          <tbody>
            {comparison.factors.map((row) => {
              const byId = Object.fromEntries(
                row.values.map((v) => [v.vehicle_id, v]),
              );
              return (
                <tr
                  key={row.factor}
                  className="border-b border-border last:border-0"
                >
                  <td className="px-3 py-3 align-top capitalize">
                    <span className="font-medium">
                      {factorDisplayName(row.factor)}
                    </span>
                    {row.note && (
                      <span className="mt-1 block text-xs text-muted-foreground">
                        {row.note}
                      </span>
                    )}
                  </td>
                  {comparison.vehicles.map((v) => {
                    const cell = byId[v.id];
                    const isWinner = row.winner_vehicle_id === v.id;
                    return (
                      <td
                        key={v.id}
                        className={`px-3 py-3 align-top ${
                          isWinner
                            ? "bg-emerald-50 font-medium text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100"
                            : ""
                        }`}
                      >
                        {cell?.display ?? "—"}
                        {isWinner ? (
                          <span className="ml-1 text-xs text-emerald-700 dark:text-emerald-300">
                            ✓
                          </span>
                        ) : null}
                      </td>
                    );
                  })}
                  <td className="px-3 py-3 align-top text-xs uppercase tracking-wide text-muted-foreground">
                    {row.reliability}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
