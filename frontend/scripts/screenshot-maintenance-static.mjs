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
  "sample-maintenance.json",
);
const outPath = path.join(
  "C:",
  "Users",
  "Administrator",
  "Desktop",
  "AI_BOT",
  "docs",
  "screenshots",
  "maintenance-checklist.png",
);

const data = JSON.parse(fs.readFileSync(jsonPath, "utf8").replace(/^\uFEFF/, ""));
const esc = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

const grouped = data.checklist.reduce((acc, item) => {
  if (!acc[item.category]) acc[item.category] = [];
  acc[item.category].push(item);
  return acc;
}, {});

const checklistHtml = Object.entries(grouped)
  .map(
    ([category, items]) => `<section style="margin-top:20px">
      <h3 style="margin:0 0 10px;font-size:14px;font-weight:600">${esc(category)}</h3>
      <ul style="list-style:none;margin:0;padding:0;display:grid;gap:8px">
        ${items
          .map(
            (item) => `<li style="border:1px solid #e8e4dc;border-radius:10px;background:#f5f3ef;padding:12px">
              <div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">
                <strong style="font-size:14px">${esc(item.item)}</strong>
                <span style="border:1px solid #e8e4dc;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:700;text-transform:uppercase;color:#6b7280">${esc(item.source)}</span>
              </div>
              <p style="margin:0;font-size:12px;line-height:1.5;color:#6b7280">${esc(item.reason)}</p>
            </li>`,
          )
          .join("")}
      </ul>
    </section>`,
  )
  .join("");

const excerpts = (data.knowledge_excerpts || [])
  .map(
    (e) => `<li style="border:1px solid #e8e4dc;border-radius:10px;background:#f5f3ef;padding:12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:4px">
        <strong style="font-size:14px">${esc(e.title)}</strong>
        <span style="font-size:11px;color:#6b7280">similarity ${Math.round(e.similarity * 100)}%</span>
      </div>
      <p style="margin:0;font-size:12px;line-height:1.5;color:#6b7280">${esc(e.content)}</p>
    </li>`,
  )
  .join("");

const v = data.vehicle;
const vehicleLabel = [v.make, v.model].filter(Boolean).join(" ") + ` · ${v.year} · ${(v.mileage_km || 0).toLocaleString()} km`;

const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>AutoAI — Maintenance checklist</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;font-family:'DM Sans',sans-serif;background:#faf9f7;color:#1a1f2e">
<header style="border-bottom:1px solid #e8e4dc;padding:14px 24px;display:flex;justify-content:space-between;max-width:860px;margin:0 auto">
  <div><strong style="font-size:18px">AutoAI</strong> <span style="color:#6b7280;font-size:12px;margin-left:8px">Car buying assistant</span></div>
  <nav style="font-size:14px;color:#6b7280">Find a car · Analyze listing · Ask a question · <span style="color:#1a1f2e">Maintenance</span></nav>
</header>
<main style="max-width:760px;margin:0 auto;padding:36px 24px 64px">
  <p style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#6b7280;margin:0 0 8px">Maintenance</p>
  <h1 style="font-size:36px;margin:0 0 10px;letter-spacing:-.02em">Maintenance checklist</h1>
  <p style="color:#6b7280;font-size:15px;line-height:1.55;max-width:540px">Describe a vehicle and get a general checklist from typical service intervals.</p>
  <div style="margin-top:16px;border:1px solid #e8e4dc;border-radius:10px;background:#fff;padding:14px 16px;font-size:14px">2018 Honda Civic with 100,000 km</div>
  <div style="display:inline-block;margin-top:12px;background:#1e293b;color:#fff;border-radius:8px;padding:10px 14px;font-size:14px;font-weight:600">Check maintenance</div>
  <hr style="border:none;border-top:1px solid #e8e4dc;margin:28px 0" />
  <section>
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">
      <h2 style="font-size:18px;margin:0">Maintenance checklist</h2>
      <span style="border:1px solid #e8e4dc;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:700;text-transform:uppercase;color:#6b7280">from description</span>
    </div>
    <p style="font-size:14px;color:#6b7280;margin:0 0 10px">${esc(vehicleLabel)}</p>
    <p style="border:1px solid #fde68a;background:#fffbeb;border-radius:10px;padding:10px 12px;font-size:12px;color:#78350f;line-height:1.5;margin:0">${esc(data.disclaimer)}</p>
  </section>
  ${checklistHtml}
  <section style="margin-top:28px">
    <h3 style="font-size:14px;margin:0 0 10px">Related knowledge</h3>
    <ul style="list-style:none;margin:0;padding:0">${excerpts}</ul>
  </section>
</main>
<footer style="border-top:1px solid #e8e4dc;padding:20px 24px;color:#6b7280;font-size:13px;max-width:860px;margin:0 auto">Independent proof of concept — not affiliated with or endorsed by PakWheels.</footer>
</body></html>`;

const htmlPath = path.join(path.dirname(outPath), "maintenance-checklist.html");
fs.writeFileSync(htmlPath, html, "utf8");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 2400 } });
await page.goto("file://" + htmlPath.replace(/\\/g, "/"), { waitUntil: "networkidle" });
await page.waitForTimeout(400);
await page.screenshot({ path: outPath, fullPage: true });
await browser.close();
console.log("wrote", outPath);
