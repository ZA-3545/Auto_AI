import { chromium } from "playwright-core";
import path from "path";
import fs from "fs";

const SAMPLE = `2019 Toyota Corolla Altis, 75,000 km, Lahore, PKR 42 lakh.
Automatic, petrol. Single owner claimed. Accident free, original paint.
Urgent sale — leaving country.`;

const outDir = path.join(
  "C:",
  "Users",
  "Administrator",
  "Desktop",
  "AI_BOT",
  "docs",
  "screenshots",
);
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, "listing-analyzer.png");

const browser = await chromium.launch({
  channel: "chrome",
  headless: true,
});
const page = await browser.newPage({
  viewport: { width: 1280, height: 2000 },
});
page.on("console", (msg) => console.log("BROWSER:", msg.type(), msg.text()));
page.on("response", (res) => {
  if (res.url().includes("/api/")) {
    console.log("API", res.status(), res.url());
  }
});

await page.goto("http://127.0.0.1:3000/analyze", {
  waitUntil: "networkidle",
  timeout: 60000,
});
await page.locator("textarea").fill(SAMPLE);
const analyzePromise = page.waitForResponse(
  (res) => res.url().includes("/api/listings/analyze") && res.request().method() === "POST",
  { timeout: 120000 },
);
await page.getByRole("button", { name: /Analyze listing/i }).click();
const apiRes = await analyzePromise;
console.log("analyze status", apiRes.status());
await page.getByText("Price assessment", { timeout: 30000 }).waitFor();
await page.waitForTimeout(1000);
await page.screenshot({ path: outPath, fullPage: true });
await browser.close();
console.log("wrote", outPath);
