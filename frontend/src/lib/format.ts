import type { ExtractedRequirements, FactorScores } from "@/lib/api";

export function formatPkr(price: number): string {
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
  }).format(price);
}

export function formatLakh(price: number): string {
  const lakh = price / 100_000;
  if (lakh >= 100) {
    const crore = lakh / 100;
    return `${crore % 1 === 0 ? crore.toFixed(0) : crore.toFixed(1)} crore`;
  }
  return `${lakh % 1 === 0 ? lakh.toFixed(0) : lakh.toFixed(1)} lakh`;
}

export function formatMileage(km: number): string {
  return `${km.toLocaleString("en-PK")} km`;
}

export function capitalize(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export type RequirementChip = { label: string; value: string };

export function requirementChips(
  requirements: ExtractedRequirements,
): RequirementChip[] {
  const chips: RequirementChip[] = [];

  if (requirements.budget_max != null && requirements.budget_min != null) {
    chips.push({
      label: "Budget",
      value: `${formatLakh(requirements.budget_min)} – ${formatLakh(requirements.budget_max)}`,
    });
  } else if (requirements.budget_max != null) {
    chips.push({
      label: "Budget",
      value: `up to ${formatLakh(requirements.budget_max)}`,
    });
  } else if (requirements.budget_min != null) {
    chips.push({
      label: "Budget",
      value: `from ${formatLakh(requirements.budget_min)}`,
    });
  }

  if (requirements.city) {
    chips.push({ label: "City", value: requirements.city });
  }
  if (requirements.transmission) {
    chips.push({
      label: "Transmission",
      value: capitalize(requirements.transmission),
    });
  }
  if (requirements.condition) {
    chips.push({
      label: "Condition",
      value: capitalize(requirements.condition),
    });
  }
  if (requirements.body_type) {
    chips.push({
      label: "Body",
      value: capitalize(requirements.body_type),
    });
  }
  if (requirements.purpose) {
    chips.push({
      label: "Purpose",
      value: capitalize(requirements.purpose),
    });
  }
  if (requirements.fuel_priority) {
    chips.push({ label: "Priority", value: "Fuel economy" });
  }
  if (requirements.resale_priority) {
    chips.push({ label: "Priority", value: "Resale value" });
  }

  return chips;
}

export function hasAnyRequirements(
  requirements: ExtractedRequirements,
): boolean {
  return requirementChips(requirements).length > 0;
}

const FACTOR_LABELS: Record<keyof FactorScores, string> = {
  budget_fit: "Budget fit",
  purpose_suitability: "Purpose fit",
  fuel_economy: "Fuel economy",
  resale: "Resale",
  mileage_condition: "Mileage & condition",
};

export function prosAndConsFromScores(scores: FactorScores): {
  pros: string[];
  cons: string[];
} {
  const pros: string[] = [];
  const cons: string[] = [];

  (Object.keys(FACTOR_LABELS) as (keyof FactorScores)[]).forEach((key) => {
    const score = scores[key];
    const label = FACTOR_LABELS[key];
    if (score >= 70) pros.push(label);
    else if (score < 45) cons.push(label);
  });

  return {
    pros: pros.slice(0, 3),
    cons: cons.slice(0, 3),
  };
}

export function factorDisplayName(name: string): string {
  return name.replaceAll("_", " ");
}

export const QUICK_PROMPTS = [
  "Best car under 30 lakh",
  "Family car",
  "Best fuel average",
  "Automatic cars",
  "Best resale",
  "Compare two cars",
] as const;
