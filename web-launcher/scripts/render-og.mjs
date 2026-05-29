import { chromium } from '/Users/ankursharma4838/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { existsSync, copyFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const templatePath = resolve(__dirname, 'og-template.html');
const publicOut = resolve(__dirname, '..', 'public', 'og-image.png');
const distDir = resolve(__dirname, '..', 'dist');
const distOut = resolve(distDir, 'og-image.png');
const tmpOut = resolve(__dirname, '.og-2x.png');

if (!existsSync(templatePath)) {
  console.error('Template missing:', templatePath);
  process.exit(1);
}

const browser = await chromium.launch({
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
});
const ctx = await browser.newContext({
  viewport: { width: 1200, height: 630 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();
await page.goto('file://' + templatePath, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(500);

await page.screenshot({
  path: tmpOut,
  type: 'png',
  omitBackground: false,
  clip: { x: 0, y: 0, width: 1200, height: 630 },
});

await browser.close();

// downsample 2x -> 1x for proper 1200x630 OG dimensions with high quality
execFileSync('sips', ['-z', '630', '1200', '-s', 'format', 'png', tmpOut, '--out', publicOut], { stdio: 'inherit' });

if (existsSync(distDir)) {
  copyFileSync(publicOut, distOut);
}

console.log('Wrote', publicOut);
