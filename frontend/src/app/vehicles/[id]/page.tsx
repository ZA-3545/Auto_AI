"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { VehicleDetailView } from "@/components/vehicle-detail-view";
import { fetchVehicleById, type Vehicle } from "@/lib/api";

export default function VehicleDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const [vehicle, setVehicle] = useState<Vehicle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!Number.isFinite(id) || id < 1) {
      setError("Invalid vehicle id.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchVehicleById(id)
      .then((data) => {
        if (!cancelled) setVehicle(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setVehicle(null);
          setError(err instanceof Error ? err.message : "Failed to load vehicle");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <div className="flex min-h-full flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:px-6">
        <Link
          href="/vehicles"
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to catalog
        </Link>

        {loading ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading vehicle details…
          </p>
        ) : null}

        {error ? (
          <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        {vehicle ? (
          <VehicleDetailView
            vehicle={vehicle}
            catalogNote="Demo catalog listing only. Independent proof of concept — not affiliated with PakWheels."
          />
        ) : null}
      </main>
      <SiteFooter />
    </div>
  );
}
