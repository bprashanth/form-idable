import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const PROD = process.env.FORMIDABLE_PROD_URL
const USERNAME = process.env.FORMIDABLE_PROD_USERNAME
const PASSWORD = process.env.FORMIDABLE_PROD_PASSWORD
const ROOT = path.resolve(import.meta.dirname, '../..')
const STATE = process.env.FORMIDABLE_PROD_SWEEP_STATE
  ? path.resolve(ROOT, process.env.FORMIDABLE_PROD_SWEEP_STATE)
  : path.join(ROOT, 'benchmarks/high_runs/prod_additive_v1/state.json')
const SCREENSHOTS = path.join(ROOT, 'benchmarks/high_visuals/prod-builder-v1')
const jobs = fs.existsSync(STATE)
  ? Object.values(JSON.parse(fs.readFileSync(STATE, 'utf8')).jobs)
    .filter(item => item.status === 'complete')
    .sort((a, b) => a.fixture.localeCompare(b.fixture))
  : []

async function signIn(page) {
  await page.goto(`${PROD}/login`)
  await page.locator('input[type="email"]').fill(USERNAME)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page.locator('[data-testid="submission-log"]')).toBeVisible({ timeout: 30_000 })
}

test.describe('production all-form QR OMR builder gate', () => {
  test.describe.configure({ mode: 'serial' })
  test.skip(!PROD || !USERNAME || !PASSWORD || jobs.length === 0,
    'Production credentials or completed production sweep state were not supplied')

  for (const job of jobs) {
    test(`${job.fixture} becomes a live empty geometry template`, async ({ page }) => {
      test.setTimeout(120_000)
      await signIn(page)
      const reviewResponse = page.waitForResponse(response =>
        response.url().includes(`/api/jobs/${job.job_id}/review-manifest`) && response.ok())
      await page.goto(`${PROD}/builder/${job.job_id}`)
      const review = await reviewResponse.then(response => response.json())
      const preview = page.locator('[data-testid="builder-preview"]')
      await expect(preview).toBeVisible({ timeout: 30_000 })
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
      const contexts = new Set(review.cells.map(cell => cell.context).filter(Boolean))
      const labels = await preview.locator('thead th').allTextContents()
      if (contexts.size >= 2) expect(labels.every(label => contexts.has(label))).toBe(true)

      fs.mkdirSync(SCREENSHOTS, { recursive: true })
      await page.screenshot({
        path: path.join(SCREENSHOTS, `${job.fixture}.png`), fullPage: true,
      })
    })
  }
})
