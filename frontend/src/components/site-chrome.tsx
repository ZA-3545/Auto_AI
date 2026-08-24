import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-border/80 bg-background/90 backdrop-blur-sm">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-lg font-semibold tracking-tight">AutoAI</span>
          <span className="hidden text-xs text-muted-foreground sm:inline">
            Car buying assistant
          </span>
        </Link>
        <nav className="flex items-center gap-3 text-sm">
          <Link
            href="/recommend"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Find a car
          </Link>
          <Link
            href="/analyze"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Analyze listing
          </Link>
          <Link
            href="/knowledge"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Ask a question
          </Link>
          <Link
            href="/advice"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            Buying advice
          </Link>
          <Link
            href="/maintenance"
            className="hidden text-muted-foreground transition-colors hover:text-foreground sm:inline"
          >
            Maintenance
          </Link>
          <Link
            href="/vehicles"
            className="hidden text-muted-foreground transition-colors hover:text-foreground sm:inline"
          >
            Browse catalog
          </Link>
          <Link
            href="/admin/metrics"
            className="hidden text-xs text-muted-foreground/70 transition-colors hover:text-muted-foreground lg:inline"
          >
            Metrics
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-border/80 bg-muted/30">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-muted-foreground sm:px-6 sm:flex-row sm:items-center sm:justify-between">
        <p>
          Independent proof of concept — not affiliated with or endorsed by
          PakWheels.
        </p>
        <p className="text-xs">Demo catalog only. Advice is informational.</p>
      </div>
    </footer>
  );
}
