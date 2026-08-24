"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink, Loader2, Wrench } from "lucide-react";

import { MaintenanceChecklistView } from "@/components/maintenance-checklist-view";
import { Button } from "@/components/ui/button";
import {
  fetchMaintenanceChecklist,
  type MaintenanceResponse,
  type RecommendedVehicle,
} from "@/lib/api";
import {
  capitalize,
  formatLakh,
  formatMileage,
  formatPkr,
  prosAndConsFromScores,
} from "@/lib/format";

type Props = {
  item: RecommendedVehicle;
  rank: number;
  selected: boolean;
  onToggleSelect: () => void;
  selectDisabled?: boolean;
};

function MatchScore({ score }: { score: number }) {
  const rounded = Math.round(score);
  const tone =
    rounded >= 75
      ? "bg-emerald-600 text-white"
      : rounded >= 55
        ? "bg-sky-700 text-white"
        : "bg-muted text-foreground";

  return (
    <div className="flex flex-col items-end gap-1">
      <span
        className={`inline-flex min-w-14 items-center justify-center rounded-md px-2 py-1 text-sm font-semibold tabular-nums ${tone}`}
      >
        {rounded}
      </span>
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-foreground/70"
          style={{ width: `${Math.min(100, Math.max(0, rounded))}%` }}
        />
      </div>
      <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
        Match
      </span>
    </div>
  );
}

export function RecommendationCard({
  item,
  rank,
  selected,
  onToggleSelect,
  selectDisabled,
}: Props) {
  const [whyOpen, setWhyOpen] = useState(false);
  const [maintenanceOpen, setMaintenanceOpen] = useState(false);
  const [maintenance, setMaintenance] = useState<MaintenanceResponse | null>(
    null,
  );
  const [maintenanceLoading, setMaintenanceLoading] = useState(false);
  const [maintenanceError, setMaintenanceError] = useState<string | null>(null);
  const { vehicle, match_score, factor_scores, explanation } = item;
  const { pros, cons } = prosAndConsFromScores(factor_scores);

  async function onCheckMaintenance() {
    if (maintenance && maintenanceOpen) {
      setMaintenanceOpen(false);
      return;
    }
    setMaintenanceOpen(true);
    if (maintenance) return;

    setMaintenanceLoading(true);
    setMaintenanceError(null);
    try {
      const data = await fetchMaintenanceChecklist({ vehicle_id: vehicle.id });
      setMaintenance(data);
    } catch (err) {
      setMaintenanceError(
        err instanceof Error ? err.message : "Maintenance check failed",
      );
    } finally {
      setMaintenanceLoading(false);
    }
  }

  return (
    <article
      className={`rounded-xl border p-4 transition-colors sm:p-5 ${
        selected
          ? "border-foreground/40 bg-muted/30"
          : "border-border bg-card"
      }`}
    >
      <div className="flex items-start gap-3">
        <label className="mt-1 flex shrink-0 cursor-pointer items-center">
          <input
            type="checkbox"
            className="size-4 accent-foreground"
            checked={selected}
            onChange={onToggleSelect}
            disabled={selectDisabled && !selected}
            aria-label={`Select ${vehicle.make} ${vehicle.model} for comparison`}
          />
        </label>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 space-y-1">
              <p className="text-xs text-muted-foreground">Option #{rank}</p>
              <h3 className="text-lg font-semibold tracking-tight sm:text-xl">
                {vehicle.make} {vehicle.model}
              </h3>
              <p className="text-sm text-muted-foreground">
                {vehicle.year} · {vehicle.city} · {capitalize(vehicle.condition)}
              </p>
            </div>
            <div className="flex items-start gap-4">
              <div className="text-right">
                <p className="text-lg font-semibold tabular-nums">
                  {formatPkr(vehicle.price)}
                </p>
                <p className="text-xs text-muted-foreground">
                  ~{formatLakh(vehicle.price)}
                </p>
              </div>
              <MatchScore score={match_score} />
            </div>
          </div>

          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-3 lg:grid-cols-5">
            <div>
              <dt className="text-xs text-muted-foreground">Transmission</dt>
              <dd className="font-medium capitalize">{vehicle.transmission}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Fuel</dt>
              <dd className="font-medium capitalize">{vehicle.fuel_type}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Engine</dt>
              <dd className="font-medium">
                {vehicle.engine_capacity != null
                  ? `${vehicle.engine_capacity} cc`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Mileage</dt>
              <dd className="font-medium">
                {formatMileage(vehicle.mileage_km)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Body</dt>
              <dd className="font-medium capitalize">{vehicle.body_type}</dd>
            </div>
          </dl>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Stronger fits
              </p>
              {pros.length > 0 ? (
                <ul className="mt-1 space-y-0.5 text-sm">
                  {pros.map((p) => (
                    <li key={p} className="text-emerald-800 dark:text-emerald-300">
                      + {p}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-sm text-muted-foreground">
                  No standout strengths vs your filters
                </p>
              )}
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Weaker fits
              </p>
              {cons.length > 0 ? (
                <ul className="mt-1 space-y-0.5 text-sm">
                  {cons.map((c) => (
                    <li key={c} className="text-amber-800 dark:text-amber-300">
                      − {c}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-1 text-sm text-muted-foreground">
                  No major weak spots vs your filters
                </p>
              )}
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setWhyOpen((open) => !open)}
            >
              {whyOpen ? (
                <ChevronUp data-icon="inline-start" />
              ) : (
                <ChevronDown data-icon="inline-start" />
              )}
              Why this car?
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void onCheckMaintenance()}
              disabled={maintenanceLoading}
            >
              {maintenanceLoading ? (
                <Loader2 className="animate-spin" data-icon="inline-start" />
              ) : (
                <Wrench data-icon="inline-start" />
              )}
              {maintenanceOpen ? "Hide maintenance" : "Check maintenance"}
            </Button>
            <Button type="button" variant="outline" size="sm" asChild>
              <Link href={`/vehicles/${vehicle.id}`}>
                <ExternalLink data-icon="inline-start" />
                View full details
              </Link>
            </Button>
            {whyOpen && (
              <div className="mt-3 space-y-3 rounded-lg border border-border bg-muted/20 p-3 text-sm">
                <p className="leading-relaxed text-muted-foreground">
                  {explanation}
                </p>
                <dl className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-5">
                  {(
                    [
                      ["Budget", factor_scores.budget_fit],
                      ["Purpose", factor_scores.purpose_suitability],
                      ["Fuel", factor_scores.fuel_economy],
                      ["Resale", factor_scores.resale],
                      ["Mileage", factor_scores.mileage_condition],
                    ] as const
                  ).map(([label, score]) => (
                    <div key={label}>
                      <dt className="text-muted-foreground">{label}</dt>
                      <dd className="font-medium tabular-nums">
                        {Math.round(score)}/100
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
            {maintenanceOpen && (
              <div className="mt-3 w-full basis-full">
                {maintenanceLoading && !maintenance ? (
                  <p className="rounded-lg border border-border bg-muted/20 p-3 text-sm text-muted-foreground">
                    Building maintenance checklist…
                  </p>
                ) : null}
                {maintenanceError ? (
                  <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                    {maintenanceError}
                  </p>
                ) : null}
                {maintenance ? (
                  <MaintenanceChecklistView result={maintenance} compact />
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
