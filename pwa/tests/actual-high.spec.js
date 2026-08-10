import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(import.meta.dirname, '../..')
const RUN = path.join(ROOT, 'benchmarks/high_runs/smoke_eval13')
const JOB = 'actual-high-eval13'

test('actual high artifacts preserve layout and focus human attention', async ({ page }) => {
  const manifest = fs.readFileSync(path.join(RUN, 'crops_manifest.json'), 'utf8')
  const review = fs.readFileSync(path.join(RUN, 'review_manifest.json'), 'utf8')
  const analytics = fs.readFileSync(path.join(RUN, 'analytics.json'), 'utf8')
  const workbook = fs.readFileSync(path.join(RUN, 'output.xlsx'))

  await page.route(`**/api/jobs/${JOB}/manifest`, route => route.fulfill({
    status: 200, contentType: 'application/json', body: manifest,
  }))
  await page.route(`**/api/jobs/${JOB}/review-manifest`, route => route.fulfill({
    status: 200, contentType: 'application/json', body: review,
  }))
  await page.route(`**/api/jobs/${JOB}/analytics`, route => route.fulfill({
    status: 200, contentType: 'application/json', body: analytics,
  }))
  await page.route(`**/api/jobs/${JOB}/xlsx`, route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ url: '/actual-high.xlsx', filename: 'SaplingSurvivalMonitoring.xlsx' }),
  }))
  await page.route('**/actual-high.xlsx', route => route.fulfill({
    status: 200,
    contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    body: workbook,
  }))
  await page.route(`**/api/jobs/${JOB}/pages/page_*.png`, route => {
    const filename = new URL(route.request().url()).pathname.split('/').pop()
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ url: `/actual-pages/${filename}` }) })
  })
  await page.route('**/actual-pages/page_*.png', route => {
    const filename = new URL(route.request().url()).pathname.split('/').pop()
    return route.fulfill({ status: 200, contentType: 'image/png',
      body: fs.readFileSync(path.join(RUN, 'pages', filename)) })
  })

  await page.goto(`/review/${JOB}`)
  await expect(page.locator('[data-testid="page-img-1"]')).toBeVisible({ timeout: 15_000 })
  await expect(page.locator('[data-testid="review-summary"]')).toContainText('Transcription 24')
  await expect(page.locator('[data-testid="review-summary"]')).toContainText('Ecology 10')
  await expect(page.locator('[data-testid^="attention-"]').first()).toBeVisible()
  await expect(page.locator('[data-testid^="ecology-overlay-"]').first()).toBeVisible()
  await expect(page.locator('[data-testid="xlsx-panel"]')).toContainText('Matha Junction Plot Data Table')
  await page.screenshot({ path: path.join(ROOT, 'benchmarks/high_visuals/actual-eval13-review.png'), fullPage: true })

  await page.locator('[data-testid="analytics-nav"]').click()
  await expect(page).toHaveURL(`/analytics/${JOB}`)
  await expect(page.locator('[data-testid="analytics-view"]')).toContainText('831')
  await expect(page.locator('[data-testid="categorical-chart"]').first()).toBeVisible()
  await page.screenshot({ path: path.join(ROOT, 'benchmarks/high_visuals/actual-eval13-analytics.png'), fullPage: true })
})
