import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(import.meta.dirname, '../..')
const SWEEP = process.env.HIGH_SWEEP_ROOT
  ? path.resolve(process.env.HIGH_SWEEP_ROOT)
  : path.join(ROOT, 'benchmarks/high_runs/additive_v1')
const SCREENSHOTS = path.join(ROOT, 'benchmarks/high_visuals/builder-v1')
const runs = fs.existsSync(SWEEP)
  ? fs.readdirSync(SWEEP).filter(name => /^eval_\d+$/.test(name))
    .filter(name => ['crops_manifest.json', 'review_manifest.json', 'output.xlsx']
      .every(file => fs.existsSync(path.join(SWEEP, name, file)))).sort()
  : []

function serveRun(page, name) {
  const root = path.join(SWEEP, name)
  const job = `builder-${name}`
  page.route('**/api/jobs', route => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify([{
      job_id: job, name: `${name}.pdf`, status: 'complete', effort: 'high', pages: 1,
    }]),
  }))
  for (const [suffix, file] of [
    ['manifest', 'crops_manifest.json'], ['review-manifest', 'review_manifest.json'],
  ]) {
    page.route(`**/api/jobs/${job}/${suffix}`, route => route.fulfill({
      status: 200, contentType: 'application/json', body: fs.readFileSync(path.join(root, file)),
    }))
  }
  page.route(`**/api/jobs/${job}/xlsx`, route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ url: `/builder-artifacts/${name}.xlsx`, filename: `${name}.xlsx` }),
  }))
  page.route(`**/builder-artifacts/${name}.xlsx`, route => route.fulfill({
    status: 200,
    contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    body: fs.readFileSync(path.join(root, 'output.xlsx')),
  }))
  return job
}

test.describe('all-form QR OMR builder gate', () => {
  test.skip(runs.length === 0, 'No completed high sweep artifacts')

  for (const name of runs) {
    test(`${name} becomes an empty printable geometry template`, async ({ page }) => {
      const job = serveRun(page, name)
      await page.goto(`/builder/${job}`)
      const preview = page.locator('[data-testid="builder-preview"]')
      await expect(preview).toBeVisible({ timeout: 15_000 })
      await expect(page.locator('[data-testid="builder-qr"]')).toHaveAttribute(
        'src', /^data:image\/png/)
      const rows = await preview.locator('tbody tr').count()
      const columns = await preview.locator('thead th').count()
      expect(rows).toBeGreaterThanOrEqual(10)
      expect(columns).toBeGreaterThanOrEqual(2)
      await expect(page.locator('[data-testid="omr-left-marks"] span')).toHaveCount(rows + 2)
      await expect(page.locator('[data-testid="omr-right-marks"] span')).toHaveCount(rows + 2)
      await expect(page.locator('[data-testid="omr-column-marks"] span')).toHaveCount(columns + 1)
      const written = await preview.locator('tbody td').evaluateAll(cells =>
        cells.map(cell => cell.textContent.trim()).filter(Boolean))
      expect(written.every(value => /^\d+$/.test(value))).toBe(true)
      const review = JSON.parse(fs.readFileSync(path.join(SWEEP, name, 'review_manifest.json')))
      const contexts = new Set(review.cells.map(cell => cell.context).filter(Boolean))
      const labels = await preview.locator('thead th').allTextContents()
      if (contexts.size >= 2) expect(labels.every(label => contexts.has(label))).toBe(true)
      fs.mkdirSync(SCREENSHOTS, { recursive: true })
      await page.screenshot({ path: path.join(SCREENSHOTS, `${name}.png`), fullPage: true })
    })
  }
})
