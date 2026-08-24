"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Button } from "@/components/ui/button";
import {
  searchVehicles,
  type Vehicle,
  type VehicleSearchResponse,
} from "@/lib/api";
import { formatPkr } from "@/lib/format";

type Filters = {
  budget_min: string;
  budget_max: string;
  city: string;
  condition: string;
  transmission: string;
  body_type: string;
  fuel_priority: boolean;
  sort_by: "price" | "year" | "mileage";
  sort_order: "asc" | "desc";
};

const INITIAL: Filters = {
  budget_min: "",
  budget_max: "",
  city: "",
  condition: "",
  transmission: "",
  body_type: "",
  fuel_priority: false,
  sort_by: "price",
  sort_order: "asc",
};

const PAGE_SIZE = 12;

export default function VehiclesPage() {
  const [filters, setFilters] = useState<Filters>(INITIAL);
  const [applied, setApplied] = useState<Filters>(INITIAL);
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<VehicleSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (nextFilters: Filters, nextOffset: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await searchVehicles({
        budget_min: nextFilters.budget_min
          ? Number(nextFilters.budget_min)
          : undefined,
        budget_max: nextFilters.budget_max
          ? Number(nextFilters.budget_max)
          : undefined,
        city: nextFilters.city || undefined,
        condition: nextFilters.condition || undefined,
        transmission: nextFilters.transmission || undefined,
        body_type: nextFilters.body_type || undefined,
        fuel_priority: nextFilters.fuel_priority,
        sort_by: nextFilters.sort_by,
        sort_order: nextFilters.sort_order,
        limit: PAGE_SIZE,
        offset: nextOffset,
      });
      setData(result);
      setOffset(nextOffset);
    } catch (err) {
      setData(null);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(INITIAL, 0);
  }, [load]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setApplied(filters);
    void load(filters, 0);
  }

  const total = data?.total ?? 0;
  const items: Vehicle[] = data?.items ?? [];
  const canPrev = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <SiteHeader />
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">
          <Link href="/" className="underline-offset-4 hover:underline">
            AutoAI
          </Link>{" "}
          · Demo catalog
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Search vehicles</h1>
        <p className="max-w-2xl text-muted-foreground">
          Deterministic filter search against the demo catalog. Sample data only —
          independent proof of concept, not affiliated with or endorsed by PakWheels.
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="grid gap-3 rounded-xl border border-border p-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Budget min (PKR)</span>
          <input
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            type="number"
            min={0}
            value={filters.budget_min}
            onChange={(e) =>
              setFilters((f) => ({ ...f, budget_min: e.target.value }))
            }
            placeholder="e.g. 2000000"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Budget max (PKR)</span>
          <input
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            type="number"
            min={0}
            value={filters.budget_max}
            onChange={(e) =>
              setFilters((f) => ({ ...f, budget_max: e.target.value }))
            }
            placeholder="e.g. 5000000"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">City</span>
          <input
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={filters.city}
            onChange={(e) => setFilters((f) => ({ ...f, city: e.target.value }))}
            placeholder="Lahore"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Condition</span>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={filters.condition}
            onChange={(e) =>
              setFilters((f) => ({ ...f, condition: e.target.value }))
            }
          >
            <option value="">Any</option>
            <option value="new">New</option>
            <option value="used">Used</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Transmission</span>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={filters.transmission}
            onChange={(e) =>
              setFilters((f) => ({ ...f, transmission: e.target.value }))
            }
          >
            <option value="">Any</option>
            <option value="automatic">Automatic</option>
            <option value="manual">Manual</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Body type</span>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={filters.body_type}
            onChange={(e) =>
              setFilters((f) => ({ ...f, body_type: e.target.value }))
            }
          >
            <option value="">Any</option>
            <option value="sedan">Sedan</option>
            <option value="hatchback">Hatchback</option>
            <option value="suv">SUV</option>
            <option value="crossover">Crossover</option>
            <option value="pickup">Pickup</option>
            <option value="van">Van</option>
            <option value="coupe">Coupe</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Sort by</span>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={filters.sort_by}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                sort_by: e.target.value as Filters["sort_by"],
              }))
            }
          >
            <option value="price">Price</option>
            <option value="year">Year</option>
            <option value="mileage">Mileage</option>
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Sort order</span>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2"
            value={filters.sort_order}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                sort_order: e.target.value as Filters["sort_order"],
              }))
            }
          >
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm sm:col-span-2">
          <input
            type="checkbox"
            checked={filters.fuel_priority}
            onChange={(e) =>
              setFilters((f) => ({ ...f, fuel_priority: e.target.checked }))
            }
          />
          Prefer better fuel average (fuel_priority)
        </label>
        <div className="flex items-end sm:col-span-2 lg:col-span-4">
          <Button type="submit" disabled={loading}>
            <Search data-icon="inline-start" />
            {loading ? "Searching…" : "Search"}
          </Button>
        </div>
      </form>

      {error && (
        <p className="text-sm text-destructive">
          {error}. Is the backend running on{" "}
          <code className="font-mono text-xs">localhost:8000</code>?
        </p>
      )}

      <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
        <p>
          {loading
            ? "Loading…"
            : `${total} result${total === 1 ? "" : "s"} · showing ${items.length} (offset ${offset})`}
        </p>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={!canPrev || loading}
            onClick={() => void load(applied, Math.max(0, offset - PAGE_SIZE))}
          >
            Previous
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={!canNext || loading}
            onClick={() => void load(applied, offset + PAGE_SIZE)}
          >
            Next
          </Button>
        </div>
      </div>

      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((vehicle) => (
          <li
            key={vehicle.id}
            className="space-y-2 rounded-xl border border-border p-4"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-semibold tracking-tight">
                  {vehicle.make} {vehicle.model}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {vehicle.year} · {vehicle.city} · {vehicle.condition}
                </p>
              </div>
              <p className="text-sm font-medium whitespace-nowrap">
                {formatPkr(vehicle.price)}
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <dt>Transmission</dt>
              <dd className="text-foreground">{vehicle.transmission}</dd>
              <dt>Body</dt>
              <dd className="text-foreground">{vehicle.body_type}</dd>
              <dt>Fuel</dt>
              <dd className="text-foreground">{vehicle.fuel_type}</dd>
              <dt>Mileage</dt>
              <dd className="text-foreground">
                {vehicle.mileage_km.toLocaleString()} km
              </dd>
              <dt>Fuel avg</dt>
              <dd className="text-foreground">
                {vehicle.fuel_average_kmpl != null
                  ? `${vehicle.fuel_average_kmpl} km/l`
                  : "—"}
              </dd>
              <dt>Resale</dt>
              <dd className="text-foreground">{vehicle.resale_rating}/5</dd>
            </dl>
            <Link
              href={`/vehicles/${vehicle.id}`}
              className="inline-flex text-sm font-medium text-foreground underline-offset-2 hover:underline"
            >
              View full details →
            </Link>
          </li>
        ))}
      </ul>

      {!loading && items.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">
          No vehicles matched these filters.
        </p>
      )}
    </div>
      <SiteFooter />
    </div>
  );
}
