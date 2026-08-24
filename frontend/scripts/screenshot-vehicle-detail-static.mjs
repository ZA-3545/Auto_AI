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
  "sample-vehicle-detail.json",
);
const outPath = path.join(
  "C:",
  "Users",
  "Administrator",
  "Desktop",
  "AI_BOT",
  "docs",
  "screenshots",
  "vehicle-detail.png",
);

const v = JSON.parse(fs.readFileSync(jsonPath, "utf8").replace(/^\uFEFF/, ""));
const esc = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

const fmtPkr = (n) =>
  new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    maximumFractionDigits: 0,
  }).format(n);

const rows = [
  ["Make", v.make],
  ["Model", v.model],
  ["Year", v.year],
  ["Price", fmtPkr(v.price)],
  ["City", v.city],
  ["Condition", v.condition],
  ["Transmission", v.transmission],
  ["Body type", v.body_type],
  ["Fuel type", v.fuel_type],
  ["Engine", v.engine_capacity ? `${v.engine_capacity.toLocaleString()} cc` : "—"],
  ["Mileage", `${v.mileage_km.toLocaleString()} km`],
  ["Fuel average", v.fuel_average_kmpl != null ? `${v.fuel_average_kmpl} km/l` : "—"],
  ["Resale rating", `${v.resale_rating} / 5`],
].map(
  ([label, value]) => `<div style="display:grid;grid-template-columns:10rem 1fr;gap:8px;border-bottom:1px solid #eceae4;padding:10px 0;font-size:14px"><dt style="color:#6b7280;margin:0">${esc(label)}</dt><dd style="margin:0;font-weight:600">${esc(value)}</dd></div>`,
).join("");

const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>AutoAI — Vehicle detail</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;font-family:'DM Sans',sans-serif;background:#faf9f7;color:#1a1f2e">
<header style="border-bottom:1px solid #e8e4dc;padding:14px 24px;max-width:760px;margin:0 auto">
  <strong style="font-size:18px">AutoAI</strong> <span style="color:#6b7280;font-size:12px">Car buying assistant</span>
</header>
<main style="max-width:760px;margin:0 auto;padding:32px 24px 64px">
  <p style="font-size:13px;color:#6b7280;margin:0 0 20px">← Back to catalog</p>
  <p style="font-size:12px;color:#6b7280;margin:0 0 6px">Catalog ID #${v.id}</p>
  <h1 style="font-size:36px;margin:0 0 6px">${esc(v.make)} ${esc(v.model)}</h1>
  <p style="color:#6b7280;font-size:16px;margin:0 0 12px">${v.year} · ${esc(v.city)} · ${esc(v.condition)}</p>
  <p style="font-size:28px;font-weight:700;margin:0 0 24px">${fmtPkr(v.price)}</p>
  <section style="border:1px solid #e8e4dc;border-radius:12px;background:#fff;padding:16px 18px">
    <h2 style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#6b7280;margin:0 0 6px">Full specifications</h2>
    <p style="font-size:11px;color:#6b7280;margin:0 0 12px">Loaded from <code style="background:#f5f3ef;padding:2px 4px;border-radius:4px">GET /api/vehicles/${v.id}</code> — deterministic catalog data</p>
    <dl style="margin:0">${rows}</dl>
  </section>
  <p style="font-size:11px;color:#6b7280;margin-top:16px">Demo catalog listing only. Independent proof of concept — not affiliated with PakWheels.</p>
</main>
</body></html>`;

const htmlPath = path.join(path.dirname(outPath), "vehicle-detail.html");
fs.writeFileSync(htmlPath, html, "utf8");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1100 } });
await page.goto("file://" + htmlPath.replace(/\\/g, "/"), { waitUntil: "networkidle" });
await page.waitForTimeout(400);
await page.screenshot({ path: outPath, fullPage: true });
await browser.close();
console.log("wrote", outPath);
