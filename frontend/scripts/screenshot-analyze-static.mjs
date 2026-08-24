import fs from "fs";
import path from "path";
import { chromium } from "playwright-core";

const jsonPath = path.join(
  "C:",
  "Users",
  "Administrator",
  "Desktop",
  "AI_BOT",
  "docs",
  "screenshots",
  "sample-analyze.json",
);
const outPath = path.join(
  "C:",
  "Users",
  "Administrator",
  "Desktop",
  "AI_BOT",
  "docs",
  "screenshots",
  "listing-analyzer.png",
);

const raw = fs.readFileSync(jsonPath, "utf8").replace(/^\uFEFF/, "");
const data = JSON.parse(raw);
const e = data.extracted;
const p = data.price_assessment;

function badge(rel) {
  const colors = {
    fact: "#ecfdf5|#064e3b|#a7f3d0",
    inference: "#fffbeb|#78350f|#fde68a",
    unknown: "#f1f5f9|#1e293b|#e2e8f0",
  };
  const [bg, fg, bd] = (colors[rel] || colors.unknown).split("|");
  return `<span style="display:inline-flex;align-items:center;border:1px solid ${bd};background:${bg};color:${fg};border-radius:4px;padding:2px 6px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em">${rel}</span>`;
}

function claimList(title, items) {
  const rows = (items || [])
    .map(
      (c) =>
        `<li style="display:flex;gap:12px;padding:8px 0;border-bottom:1px solid #e8e4dc"><div>${badge(c.reliability)}</div><p style="margin:0;font-size:14px;line-height:1.5;color:#1a1f2e">${c.text}</p></li>`,
    )
    .join("");
  return `<section style="margin-top:28px"><h3 style="margin:0 0 10px;font-size:14px">${title}</h3><ul style="list-style:none;margin:0;padding:0">${rows}</ul></section>`;
}

const fmt = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("en-PK", {
        style: "currency",
        currency: "PKR",
        maximumFractionDigits: 0,
      }).format(n);

const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>AutoAI — Analyze listing</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;font-family:'DM Sans',sans-serif;background:#faf9f7;color:#1a1f2e">
<header style="border-bottom:1px solid #e8e4dc;background:rgba(250,249,247,.92);padding:14px 24px;display:flex;justify-content:space-between;align-items:baseline;max-width:860px;margin:0 auto">
  <div><strong style="font-size:18px">AutoAI</strong> <span style="color:#6b7280;font-size:12px;margin-left:8px">Car buying assistant</span></div>
  <nav style="font-size:14px;color:#6b7280">Find a car · <span style="color:#1a1f2e">Analyze listing</span> · Browse catalog</nav>
</header>
<main style="max-width:760px;margin:0 auto;padding:36px 24px 64px">
  <p style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#6b7280;margin:0 0 8px">Listing analyzer</p>
  <h1 style="font-size:36px;margin:0 0 10px;letter-spacing:-.02em">Analyze this listing</h1>
  <p style="color:#6b7280;font-size:15px;line-height:1.55;max-width:540px;margin:0 0 24px">Paste a seller ad. We extract structured details, compare the asking price to our reference dataset, and surface labeled caveats.</p>
  <div style="border:1px solid #e8e4dc;border-radius:10px;background:#fff;padding:14px 16px;font-size:14px;line-height:1.55;white-space:pre-wrap;margin-bottom:16px">2019 Toyota Corolla Altis, 75,000 km, Lahore, PKR 42 lakh.
Automatic, petrol. Single owner claimed. Accident free, original paint.
Urgent sale — leaving country.</div>
  <div style="display:inline-block;background:#1e293b;color:#fff;border-radius:8px;padding:10px 14px;font-size:14px;font-weight:600;margin-bottom:28px">Analyze listing</div>
  <hr style="border:none;border-top:1px solid #e8e4dc;margin:28px 0" />
  <section>
    <h2 style="font-size:18px;margin:0 0 8px">Summary</h2>
    <p style="font-size:14px;line-height:1.6;margin:0">${data.advisor_summary || ""}</p>
    <p style="font-size:12px;color:#6b7280;margin:8px 0 0">Summary source: ${data.advisor_summary_source} · ${data.provider}/${data.model}</p>
  </section>
  <section style="margin-top:28px">
    <h2 style="font-size:18px;margin:0 0 12px">Extracted details</h2>
    <div style="border:1px solid #e8e4dc;border-radius:10px;background:#f5f3ef;padding:16px;display:grid;gap:8px;font-size:14px">
      <div><span style="color:#6b7280;display:inline-block;width:120px">Vehicle</span><strong>${[e.make, e.model, e.variant].filter(Boolean).join(" ")}</strong></div>
      <div><span style="color:#6b7280;display:inline-block;width:120px">Year</span><strong>${e.year ?? "—"}</strong></div>
      <div><span style="color:#6b7280;display:inline-block;width:120px">Asking price</span><strong>${fmt(e.asking_price)}</strong></div>
      <div><span style="color:#6b7280;display:inline-block;width:120px">Mileage</span><strong>${e.mileage_km != null ? e.mileage_km.toLocaleString() + " km" : "—"}</strong></div>
      <div><span style="color:#6b7280;display:inline-block;width:120px">Location</span><strong>${e.location ?? "—"}</strong></div>
    </div>
  </section>
  <section style="margin-top:28px">
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px">
      <h2 style="font-size:18px;margin:0">Price assessment</h2>
      ${badge(p.reliability)}
      <span style="border:1px solid #e8e4dc;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:700;text-transform:uppercase;color:#6b7280">${String(p.relative).replace("_", " ")}</span>
    </div>
    <p style="font-size:14px;line-height:1.55;margin:0 0 8px">${p.summary}</p>
    <p style="font-size:12px;color:#6b7280;line-height:1.5;margin:0">${p.dataset_disclaimer}</p>
    <p style="font-size:12px;color:#6b7280;margin:8px 0 0">Reference comps: ${p.reference_count}${p.reference_median != null ? " · median " + fmt(p.reference_median) : ""}</p>
  </section>
  ${claimList("Red flags", data.red_flags)}
  ${claimList("Missing information", data.missing_information)}
  <section style="margin-top:28px">
    <h3 style="margin:0 0 10px;font-size:14px">Questions to ask the seller</h3>
    <ol style="margin:0;padding-left:20px;font-size:14px;line-height:1.55">${(data.seller_questions || []).map((q) => `<li style="margin-bottom:4px">${q}</li>`).join("")}</ol>
  </section>
</main>
<footer style="border-top:1px solid #e8e4dc;padding:20px 24px;color:#6b7280;font-size:13px;max-width:860px;margin:0 auto">Independent proof of concept — not affiliated with or endorsed by PakWheels.</footer>
</body></html>`;

const htmlPath = path.join(path.dirname(outPath), "listing-analyzer.html");
fs.writeFileSync(htmlPath, html, "utf8");

const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 2200 } });
await page.goto("file://" + htmlPath.replace(/\\/g, "/"), {
  waitUntil: "networkidle",
});
await page.waitForTimeout(500);
await page.screenshot({ path: outPath, fullPage: true });
await browser.close();
console.log("wrote", outPath);
