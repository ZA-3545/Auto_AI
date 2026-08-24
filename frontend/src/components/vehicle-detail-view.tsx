import type { Vehicle } from "@/lib/api";
import {
  capitalize,
  formatLakh,
  formatMileage,
  formatPkr,
} from "@/lib/format";

type Props = {
  vehicle: Vehicle;
  catalogNote?: string;
};

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="grid grid-cols-[8.5rem_1fr] gap-2 border-b border-border/60 py-2.5 text-sm last:border-0 sm:grid-cols-[10rem_1fr]">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium text-foreground">{value}</dd>
    </div>
  );
}

export function VehicleDetailView({ vehicle, catalogNote }: Props) {
  return (
    <article className="space-y-6">
      <header className="space-y-2">
        <p className="text-xs text-muted-foreground">Catalog ID #{vehicle.id}</p>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          {vehicle.make} {vehicle.model}
        </h1>
        <p className="text-lg text-muted-foreground">
          {vehicle.year} · {vehicle.city} · {capitalize(vehicle.condition)}
        </p>
        <div className="flex flex-wrap items-baseline gap-3 pt-1">
          <p className="text-2xl font-semibold tabular-nums">
            {formatPkr(vehicle.price)}
          </p>
          <p className="text-sm text-muted-foreground">
            ~{formatLakh(vehicle.price)}
          </p>
        </div>
      </header>

      <section className="rounded-xl border border-border bg-card p-4 sm:p-5">
        <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Full specifications
        </h2>
        <p className="mb-3 text-xs text-muted-foreground">
          Loaded from{" "}
          <code className="rounded bg-muted px-1 py-0.5 font-mono text-[11px]">
            GET /api/vehicles/{vehicle.id}
          </code>{" "}
          — deterministic catalog data, not LLM-generated.
        </p>
        <dl>
          <DetailRow label="Make" value={vehicle.make} />
          <DetailRow label="Model" value={vehicle.model} />
          <DetailRow label="Year" value={String(vehicle.year)} />
          <DetailRow label="Price" value={formatPkr(vehicle.price)} />
          <DetailRow label="City" value={vehicle.city} />
          <DetailRow label="Condition" value={capitalize(vehicle.condition)} />
          <DetailRow
            label="Transmission"
            value={capitalize(vehicle.transmission)}
          />
          <DetailRow label="Body type" value={capitalize(vehicle.body_type)} />
          <DetailRow label="Fuel type" value={capitalize(vehicle.fuel_type)} />
          <DetailRow
            label="Engine"
            value={
              vehicle.engine_capacity != null
                ? `${vehicle.engine_capacity.toLocaleString()} cc`
                : "—"
            }
          />
          <DetailRow label="Mileage" value={formatMileage(vehicle.mileage_km)} />
          <DetailRow
            label="Fuel average"
            value={
              vehicle.fuel_average_kmpl != null
                ? `${vehicle.fuel_average_kmpl} km/l`
                : "—"
            }
          />
          <DetailRow
            label="Resale rating"
            value={`${vehicle.resale_rating} / 5`}
          />
          <DetailRow
            label="Listed"
            value={new Date(vehicle.created_at).toLocaleString()}
          />
        </dl>
      </section>

      {catalogNote ? (
        <p className="text-xs leading-relaxed text-muted-foreground">
          {catalogNote}
        </p>
      ) : null}
    </article>
  );
}
