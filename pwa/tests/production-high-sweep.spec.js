import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const PROD = process.env.FORMIDABLE_PROD_URL
const USERNAME = process.env.FORMIDABLE_PROD_USERNAME
const PASSWORD = process.env.FORMIDABLE_PROD_PASSWORD
const ROOT = path.resolve(import.meta.dirname, '../..')
const STATE = process.env.FORMIDABLE_PROD_SWEEP_STATE
  ? path.resolve(ROOT, process.env.FORMIDABLE_PROD_SWEEP_STATE)
  : path.join(ROOT, 'benchmarks/high_runs/prod_sweep_v1/state.json')
const sweepName = path.basename(path.dirname(STATE)).replaceAll('_', '-')
const SCREENSHOTS = path.join(ROOT, 'benchmarks/high_visuals', sweepName)
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

function coloredCell(page, pageNumber, item) {
  return page.locator(
    `[data-testid="xlsx-cell-${pageNumber}-${item.xlsx_row}-${item.xlsx_column - 1}"]`
  )
}

test.describe('production all-PDF high gate', () => {
  test.describe.configure({ mode: 'serial' })
  test.skip(!PROD || !USERNAME || !PASSWORD || jobs.length === 0,
    'Production credentials or completed production sweep state were not supplied')

  for (const job of jobs) {
    test(`${job.fixture} renders every production page and analytics`, async ({ page }) => {
      test.setTimeout(180_000)
      await signIn(page)

      const reviewResponse = page.waitForResponse(response =>
        response.url().includes(`/api/jobs/${job.job_id}/review-manifest`) && response.ok())
      const manifestResponse = page.waitForResponse(response =>
        response.url().includes(`/api/jobs/${job.job_id}/manifest`) && response.ok())
      await page.goto(`${PROD}/review/${job.job_id}`)
      const [review, manifest] = await Promise.all([
        reviewResponse.then(response => response.json()),
        manifestResponse.then(response => response.json()),
      ])

      await expect(page.locator('[data-testid="review-summary"]')).toBeVisible({ timeout: 30_000 })
      await expect(page.locator('[data-testid="xlsx-panel"] tbody tr').first())
        .toBeVisible({ timeout: 30_000 })
      expect(manifest.pages.length).toBeGreaterThan(0)

      const attention = review.views.transcription_attention
      const ecology = review.views.ecology_anomalies
      const attentionIds = new Set(attention.map(item => item.cell_id))
      const reviewCells = review.cells.filter(cell => attentionIds.has(cell.id))
      const screenshotPage = manifest.pages
        .map((_, index) => ({
          page: index + 1,
          count: attention.filter(item => Number(item.page) === index + 1).length
            + ecology.filter(item => Number(item.location?.page ?? item.page) === index + 1).length,
        }))
        .sort((a, b) => b.count - a.count)[0].page

      fs.mkdirSync(SCREENSHOTS, { recursive: true })
      for (let pageNumber = 1; pageNumber <= manifest.pages.length; pageNumber++) {
        const image = page.locator(`[data-testid="page-img-${pageNumber}"]`)
        await expect(image).toBeVisible({ timeout: 30_000 })
        await expect.poll(() => image.evaluate(element => element.naturalWidth), {
          timeout: 30_000,
        }).toBeGreaterThan(500)
        await expect.poll(() => image.evaluate(element => element.naturalHeight), {
          timeout: 30_000,
        }).toBeGreaterThan(500)
        await expect.poll(() => page.evaluate(() => {
          const current = document.querySelector('[data-testid^="page-img-"]')
          const viewport = document.querySelector('[data-testid="review-content"]')
          if (!current || !viewport) return false
          const rect = current.getBoundingClientRect()
          return rect.width <= viewport.clientWidth && rect.height <= viewport.clientHeight
        }), { timeout: 30_000 }).toBe(true)

        const pageAttention = attention.filter(item => Number(item.page) === pageNumber)
        const pageEcology = ecology.filter(
          item => Number(item.location?.page ?? item.page) === pageNumber && item.bbox?.length === 4)
        await expect(page.locator('[data-testid^="attention-"]')).toHaveCount(pageAttention.length)
        await expect(page.locator('[data-testid^="ecology-overlay-"]')).toHaveCount(pageEcology.length)

        const redCell = reviewCells.find(item => Number(item.page) === pageNumber
          && item.xlsx_row != null && item.xlsx_column != null)
        if (redCell) {
          await expect(coloredCell(page, pageNumber, redCell)).toHaveCSS(
            'background-color', 'rgba(186, 26, 26, 0.14)')
        }
        const orangeCell = ecology.find(item => Number(item.location?.page ?? item.page) === pageNumber
          && item.xlsx_row != null && item.xlsx_column != null
          && !reviewCells.some(cell => cell.page === pageNumber
            && cell.xlsx_row === item.xlsx_row && cell.xlsx_column === item.xlsx_column))
        if (orangeCell) {
          await expect(coloredCell(page, pageNumber, orangeCell)).toHaveCSS(
            'background-color', 'rgba(251, 146, 60, 0.18)')
        }

        if (pageNumber === screenshotPage) {
          await page.screenshot({
            path: path.join(SCREENSHOTS, `${job.fixture}-review.png`), fullPage: true,
          })
        }
        if (pageNumber < manifest.pages.length) {
          await page.locator('button:has(span.material-symbols-outlined:text("chevron_right"))').click()
        }
      }

      const analyticsResponse = page.waitForResponse(response =>
        response.url().includes(`/api/jobs/${job.job_id}/analytics`) && response.ok())
      await page.locator('[data-testid="analytics-nav"]').click()
      const analytics = await analyticsResponse.then(response => response.json())
      await expect(page.locator('[data-testid="analytics-view"]')).toBeVisible({ timeout: 30_000 })
      expect(analytics.summary.pages).toBe(manifest.pages.length)
      await expect(page.locator(
        '[data-testid="numeric-chart"], [data-testid="categorical-chart"]'
      ).first()).toBeVisible()
      await expect(page.locator('input, textarea, [contenteditable="true"]')).toHaveCount(0)
      await page.screenshot({
        path: path.join(SCREENSHOTS, `${job.fixture}-analytics.png`), fullPage: true,
      })
    })
  }
})
