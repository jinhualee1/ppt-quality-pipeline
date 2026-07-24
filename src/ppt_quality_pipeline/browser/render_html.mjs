import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

function parseArgs(argv) {
  const values = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) values[key] = true;
    else {
      values[key] = next;
      index += 1;
    }
  }
  return values;
}

async function loadPlaywright() {
  try {
    return await import("playwright-core");
  } catch (error) {
    const configured = process.env.PQP_PLAYWRIGHT_PATH;
    if (configured) {
      const require = createRequire(import.meta.url);
      return require(configured);
    }
    try {
      const projectRequire = createRequire(path.join(process.cwd(), "package.json"));
      return projectRequire("playwright-core");
    } catch {
      throw error;
    }
  }
}

async function findBrowser() {
  const configured = process.env.PQP_CHROME;
  const candidates = [
    configured,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      await fs.access(candidate);
      return candidate;
    } catch {}
  }
  return undefined;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input || !args.output) {
    throw new Error("Usage: node scripts/render_html.mjs --input deck.html --output pages");
  }
  const input = path.resolve(args.input);
  const output = path.resolve(args.output);
  await fs.mkdir(output, { recursive: true });
  const { chromium } = await loadPlaywright();
  const executablePath = await findBrowser();
  const browser = await chromium.launch({ headless: true, executablePath });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 1,
    });
    await page.goto(pathToFileURL(input).href, { waitUntil: "networkidle" });
    await page.evaluate(async () => {
      if (document.fonts?.ready) await document.fonts.ready;
      await Promise.all(
        [...document.images]
          .filter((image) => !image.complete)
          .map((image) => new Promise((resolve) => {
            image.addEventListener("load", resolve, { once: true });
            image.addEventListener("error", resolve, { once: true });
          })),
      );
    });
    const selector = "[data-slide]";
    let slides = page.locator(selector);
    let count = await slides.count();
    if (!count) {
      for (const fallback of [".slide", ".ppt-slide", "section"]) {
        slides = page.locator(fallback);
        count = await slides.count();
        if (count) break;
      }
    }
    const pages = [];
    if (!count) {
      const name = "page_001.png";
      await page.screenshot({ path: path.join(output, name), fullPage: true });
      pages.push(name);
    } else {
      for (let index = 0; index < count; index += 1) {
        const name = `page_${String(index + 1).padStart(3, "0")}.png`;
        const slide = slides.nth(index);
        await slide.scrollIntoViewIfNeeded();
        await slide.screenshot({ path: path.join(output, name), animations: "disabled" });
        pages.push(name);
      }
    }
    const manifest = {
      input,
      renderer: "playwright",
      selector: count ? selector : "page",
      pages,
    };
    await fs.writeFile(path.join(output, "render_manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
    process.stdout.write(`${JSON.stringify(manifest)}\n`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
