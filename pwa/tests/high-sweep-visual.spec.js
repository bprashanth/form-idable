import { test, expect } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(import.meta.dirname, '../..')
const SWEEP = process.env.HIGH_SWEEP_ROOT
  ? path.resolve(process.env.HIGH_SWEEP_ROOT)
  : path.join(ROOT, 'benchmarks/high_runs/additive_v1')
const SCREENSHOTS = path.join(ROOT, 'benchmarks/high_visuals/additive-v1')

const runs = fs.existsSync(SWEEP)
  ? fs.readdirSync(SWEEP)
    .filter(name => /^eval_\d+$/.test(name))
    .filter(name => ['crops_manifest.json', 'review_manifest.json', 'analytics.json',
      'output.xlsx'].every(file => fs.existsSync(path.join(SWEEP, name, file))))
    .sort()
  : []

function serveRun(page, name) {
  const run = path.join(SWEEP, name)
  const job = `visual-${name}`
  const jsonRoute = (suffix, file) => page.route(`**/api/jobs/${job}/${suffix}`, route =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: fs.readFileSync(path.join(run, file), 'utf8') }))
  jsonRoute('manifest', 'crops_manifest.json')
  jsonRoute('review-manifest', 'review_manifest.json')
  jsonRoute('analytics', 'analytics.json')
  page.route(`**/api/jobs/${job}/xlsx`, route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ url: `/visual-artifacts/${name}/output.xlsx`, filename: `${name}.xlsx` }),
  }))
  page.route(`**/visual-artifacts/${name}/output.xlsx`, route => route.fulfill({
    status: 200,
    contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    body: fs.readFileSync(path.join(run, 'output.xlsx')),
  }))
  page.route(`**/api/jobs/${job}/pages/page_*.png`, route => {
    const filename = new URL(route.request().url()).pathname.split('/').pop()
    return route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ url: `/visual-artifacts/${name}/${filename}` }) })
  })
  page.route(`**/visual-artifacts/${name}/page_*.png`, route => {
    const filename = new URL(route.request().url()).pathname.split('/').pop()
    return route.fulfill({ status: 200, contentType: 'image/png',
      body: fs.readFileSync(path.join(run, 'pages', filename)) })
  })
  return job
}

test.describe('all-PDF high visual gate', () => {
  test.skip(runs.length === 0, 'No completed high sweep artifacts')

  for (const name of runs) {
    test(`${name} preserves every page and exposes focused review`, async ({ page }) => {
      test.setTimeout(120_000)
      const run = path.join(SWEEP, name)
      const manifest = JSON.parse(fs.readFileSync(path.join(run, 'crops_manifest.json')))
      const review = JSON.parse(fs.readFileSync(path.join(run, 'review_manifest.json')))
      const analytics = JSON.parse(fs.readFileSync(path.join(run, 'analytics.json')))
      const job = serveRun(page, name)

      await page.goto(`/review/${job}`)
      await expect(page.locator('[data-testid="review-summary"]')).toBeVisible({ timeout: 15_000 })
      await expect(page.locator('[data-testid="xlsx-panel"]')).toBeVisible()
      await expect(page.locator('[data-testid="xlsx-panel"] tbody tr').first())
        .toBeVisible({ timeout: 15_000 })

      for (let pageNumber = 1; pageNumber <= manifest.pages.length; pageNumber++) {
        const image = page.locator(`[data-testid="page-img-${pageNumber}"]`)
        await expect(image).toBeVisible({ timeout: 15_000 })
        await expect.poll(() => image.evaluate(element => element.naturalWidth), {
          timeout: 15_000,
        }).toBeGreaterThan(500)
        const dimensions = await image.evaluate(element => ({
          width: element.naturalWidth, height: element.naturalHeight,
        }))
        expect(dimensions.width).toBeGreaterThan(500)
        expect(dimensions.height).toBeGreaterThan(500)

        const red = review.views.transcription_attention
          .filter(item => item.page === pageNumber).length
        const orange = review.views.ecology_anomalies
          .filter(item => item.page === pageNumber).length
        await expect(page.locator('[data-testid^="attention-"]')).toHaveCount(red)
        await expect(page.locator('[data-testid^="ecology-overlay-"]')).toHaveCount(orange)

        if (pageNumber < manifest.pages.length) {
          await page.locator('button:has(span.material-symbols-outlined:text("chevron_right"))').click()
        }
      }

      fs.mkdirSync(SCREENSHOTS, { recursive: true })
      await page.screenshot({ path: path.join(SCREENSHOTS, `${name}-review.png`), fullPage: true })
      await page.locator('[data-testid="analytics-nav"]').click()
      await expect(page).toHaveURL(`/analytics/${job}`)
      await expect(page.locator('[data-testid="analytics-view"]')).toBeVisible()
      expect(analytics.summary.pages).toBe(manifest.pages.length)
      await expect(page.locator(
        '[data-testid="numeric-chart"], [data-testid="categorical-chart"]'
      ).first()).toBeVisible()
      await page.screenshot({ path: path.join(SCREENSHOTS, `${name}-analytics.png`), fullPage: true })
    })
  }
})
