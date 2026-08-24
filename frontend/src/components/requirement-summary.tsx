import type { ExtractedRequirements } from "@/lib/api";
import {
  hasAnyRequirements,
  requirementChips,
} from "@/lib/format";

type Props = {
  requirements: ExtractedRequirements;
  title?: string;
  emptyHint?: string;
};

export function RequirementSummary({
  requirements,
  title = "What we understood",
  emptyHint = "Tell us your budget, city, or preferences to get started.",
}: Props) {
  const chips = requirementChips(requirements);

  if (requirements.needs_clarification && requirements.clarification_question) {
    return (
      <section className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
        <h2 className="text-sm font-medium text-amber-900 dark:text-amber-200">
          Need a quick clarification
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {requirements.clarification_question}
        </p>
        {chips.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {chips.map((chip) => (
              <span
                key={`${chip.label}-${chip.value}`}
                className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1 text-xs"
              >
                <span className="text-muted-foreground">{chip.label}:</span>
                <span className="font-medium">{chip.value}</span>
              </span>
            ))}
          </div>
        )}
      </section>
    );
  }

  if (!hasAnyRequirements(requirements)) {
    return (
      <section className="rounded-xl border border-dashed border-border p-4">
        <h2 className="text-sm font-medium">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{emptyHint}</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-border bg-card p-4">
      <h2 className="text-sm font-medium">{title}</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {chips.map((chip) => (
          <span
            key={`${chip.label}-${chip.value}`}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-muted/40 px-2.5 py-1 text-xs sm:text-sm"
          >
            <span className="text-muted-foreground">{chip.label}:</span>
            <span className="font-medium text-foreground">{chip.value}</span>
          </span>
        ))}
      </div>
    </section>
  );
}
