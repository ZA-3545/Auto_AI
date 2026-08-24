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
  "sample-admin-metrics.json",
);
const outPath = path.join(
  "C:",
  "Users",
  "Administrator",
  "Desktop",
  "AI_BOT",
  "docs",
  "screenshots",
  "admin-metrics.png",
);

const data = JSON.parse(fs.readFileSync(jsonPath, "utf8").replace(/^\uFEFF/, ""));
const esc = (s) =>
  String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

function badge(status) {
  const styles = {
    computed: "#ecfdf5|#064e3b|#a7f3d0|Computed",
    manual: "#eff6ff|#1e3a8a|#bfdbfe|Manual",
    not_available: "#f4f4f5|#52525b|#e4e4e7|Not yet available",
  };
  const [bg, fg, bd, label] = (styles[status] || styles.not_available).split("|");
  return `<span style="border:1px solid ${bd};background:${bg};color:${fg};border-radius:4px;padding:2px 6px;font-size:10px;font-weight:700;text-transform:uppercase">${label}</span>`;
}

function cards(items) {
  return items
    .map(
      (m) => `<article style="border:1px solid #e8e4dc;border-radius:12px;background:#fff;padding:14px">
        <div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:8px">
          <h3 style="margin:0;font-size:13px;font-weight:600">${esc(m.label)}</h3>
          ${badge(m.status)}
        </div>
        <p style="margin:0;font-size:24px;font-weight:700">${m.value != null ? esc(m.value) : "—"}${m.unit ? ` <span style="font-size:13px;font-weight:400;color:#6b7280">${esc(m.unit)}</span>` : ""}</p>
        ${m.detail ? `<p style="margin:8px 0 0;font-size:11px;color:#6b7280">${esc(m.detail)}</p>` : ""}
        ${m.note ? `<p style="margin:6px 0 0;font-size:11px;color:#6b7280;line-height:1.45">${esc(m.note)}</p>` : ""}
      </article>`,
    )
    .join("");
}

const computed = data.metrics.filter((m) => m.status === "computed");
const manual = data.metrics.filter((m) => m.status === "manual");
const unavailable = data.metrics.filter((m) => m.status === "not_available");

const latencyRows = (data.endpoint_latency || [])
  .map(
    (r) => `<tr style="border-bottom:1px solid #eceae4">
      <td style="padding:8px 12px;font-family:monospace;font-size:11px">${esc(r.path)}</td>
      <td style="padding:8px 12px">${r.request_count}</td>
      <td style="padding:8px 12px">${r.error_count}</td>
      <td style="padding:8px 12px">${r.avg_latency_ms ?? "—"}</td>
    </tr>`,
  )
  .join("");

const html = `<!doctype html>
<html><head><meta charset="utf-8"><title>AutoAI — Metrics dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin:0;font-family:'DM Sans',sans-serif;background:#faf9f7;color:#1a1f2e">
<header style="border-bottom:1px solid #e8e4dc;padding:14px 24px;max-width:1100px;margin:0 auto">
  <strong style="font-size:18px">AutoAI</strong> <span style="color:#6b7280;font-size:12px">Internal · Evaluation metrics</span>
</header>
<main style="max-width:1100px;margin:0 auto;padding:32px 24px 64px">
  <p style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#6b7280;margin:0 0 8px">Internal · Evaluation metrics</p>
  <h1 style="font-size:34px;margin:0 0 8px">Metrics dashboard</h1>
  <p style="color:#6b7280;font-size:14px;max-width:680px">PLANNING.md K.1 — read-only PoC reporting. Session counters reset on backend restart.</p>
  <p style="border:1px solid #fde68a;background:#fffbeb;border-radius:10px;padding:10px 12px;font-size:12px;color:#78350f;line-height:1.5;margin:16px 0 24px">Internal use only — no authentication yet. Metrics marked "Not yet available" are not fabricated (Section H).</p>
  <section style="margin-bottom:28px"><h2 style="font-size:18px;margin:0 0 12px">Computed (${computed.length})</h2>
    <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px">${cards(computed)}</div></section>
  <section style="margin-bottom:28px"><h2 style="font-size:18px;margin:0 0 12px">Manual / test suite (${manual.length})</h2>
    <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px">${cards(manual)}</div></section>
  <section style="margin-bottom:28px"><h2 style="font-size:18px;margin:0 0 12px">Not yet available (${unavailable.length})</h2>
    <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px">${cards(unavailable)}</div></section>
  <section><h2 style="font-size:18px;margin:0 0 12px">Endpoint latency</h2>
    <table style="width:100%;border-collapse:collapse;border:1px solid #e8e4dc;border-radius:12px;overflow:hidden;background:#fff;font-size:13px">
      <thead style="background:#f5f3ef;color:#6b7280;font-size:11px;text-transform:uppercase"><tr>
        <th style="padding:8px 12px;text-align:left">Path</th><th style="padding:8px 12px;text-align:left">Requests</th><th style="padding:8px 12px;text-align:left">Errors</th><th style="padding:8px 12px;text-align:left">Avg ms</th>
      </tr></thead><tbody>${latencyRows}</tbody></table></section>
</main>
<footer style="border-top:1px solid #e8e4dc;padding:20px 24px;color:#6b7280;font-size:13px;max-width:1100px;margin:0 auto">Independent proof of concept — not affiliated with PakWheels.</footer>
</body></html>`;

const htmlPath = path.join(path.dirname(outPath), "admin-metrics.html");
fs.writeFileSync(htmlPath, html, "utf8");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 2200 } });
await page.goto("file://" + htmlPath.replace(/\\/g, "/"), { waitUntil: "networkidle" });
await page.waitForTimeout(400);
await page.screenshot({ path: outPath, fullPage: true });
await browser.close();
console.log("wrote", outPath);
