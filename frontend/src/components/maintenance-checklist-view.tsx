"use client";

import type { MaintenanceResponse } from "@/lib/api";
import { formatMileage } from "@/lib/format";

type Props = {
  result: MaintenanceResponse;
  compact?: boolean;
};

function vehicleLabel(result: MaintenanceResponse): string {
  const { make, model, year, mileage_km } = result.vehicle;
  const parts = [make, model].filter(Boolean).join(" ");
  const yearPart = year != null ? String(year) : null;
  const mileagePart =
    mileage_km != null ? formatMileage(mileage_km) : null;
  return [parts || "Vehicle", yearPart, mileagePart].filter(Boolean).join(" · ");
}

export function MaintenanceChecklistView({ result, compact = false }: Props) {
  const grouped = result.checklist.reduce<Record<string, typeof result.checklist>>(
    (acc, item) => {
      if (!acc[item.category]) acc[item.category] = [];
      acc[item.category].push(item);
      return acc;
    },
    {},
  );

  return (
    <div className={compact ? "space-y-4" : "mt-10 space-y-6 border-t border-border pt-8"}>
      <section className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold tracking-tight">
            Maintenance checklist
          </h2>
          <span className="rounded border border-border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            {result.vehicle.source === "database" ? "from catalog" : "from description"}
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{vehicleLabel(result)}</p>
        <p className="rounded-lg border border-amber-200/80 bg-amber-50/80 px-3 py-2 text-xs leading-relaxed text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-100">
          {result.disclaimer}
        </p>
      </section>

      <section className="space-y-4">
        {Object.entries(grouped).map(([category, items]) => (
          <div key={category} className="space-y-2">
            <h3 className="text-sm font-semibold tracking-tight">{category}</h3>
            <ul className="space-y-2">
              {items.map((item) => (
                <li
                  key={`${category}-${item.item}`}
                  className="rounded-lg border border-border/80 bg-muted/20 p-3"
                >
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium">{item.item}</p>
                    <span className="rounded border border-border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                      {item.source}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {item.reason}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {result.knowledge_excerpts.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold tracking-tight">
            Related knowledge
          </h3>
          <ul className="space-y-3">
            {result.knowledge_excerpts.map((excerpt) => (
              <li
                key={excerpt.title}
                className="rounded-lg border border-border/80 bg-muted/20 p-3"
              >
                <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
                  <p className="text-sm font-medium">{excerpt.title}</p>
                  <span className="text-[11px] text-muted-foreground">
                    similarity {(excerpt.similarity * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {excerpt.content}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
