import { test, expect } from '@playwright/test'
import path from 'node:path'

const PROD = process.env.FORMIDABLE_PROD_URL
const USERNAME = process.env.FORMIDABLE_PROD_USERNAME
const PASSWORD = process.env.FORMIDABLE_PROD_PASSWORD
const VERIFY_JOB = process.env.FORMIDABLE_PROD_VERIFY_JOB || 'high-prod-verify'
const ROOT = path.resolve(import.meta.dirname, '../..')

test('production low/high routing and focused review', async ({ page }) => {
  test.skip(!PROD || !USERNAME || !PASSWORD, 'Production credentials were not supplied')
  test.setTimeout(120_000)

  await page.goto(`${PROD}/login`)
  await page.locator('input[type="email"]').fill(USERNAME)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign In' }).click()
  await expect(page.locator('[data-testid="submission-log"]')).toBeVisible({ timeout: 30_000 })

  await page.locator('[data-testid="add-forms-btn"]').click()
  await expect(page.locator('[data-testid="effort-picker"]')).toBeVisible()
  await expect(page.locator('[data-testid="effort-low"]')).toContainText('LOW')
  await expect(page.locator('[data-testid="effort-high"]')).toContainText('HIGH')
  await page.getByRole('button', { name: 'Cancel' }).click()

  const highRow = page.locator('[data-testid^="job-row-"]').filter({ hasText: VERIFY_JOB }).first()
  await expect(highRow).toContainText('High · dual reader')
  await highRow.click()
  await expect(page.locator('[data-testid="review-summary"]')).toBeVisible({ timeout: 30_000 })
  const pageImage = page.locator('[data-testid="page-img-1"]')
  await expect(pageImage).toBeVisible({ timeout: 30_000 })
  await expect.poll(() => pageImage.evaluate(element => element.naturalWidth), {
    timeout: 30_000,
  }).toBeGreaterThan(500)
  await expect.poll(() => page.evaluate(() => {
    const image = document.querySelector('[data-testid="page-img-1"]')
    const viewport = document.querySelector('[data-testid="review-content"]')
    if (!image || !viewport) return false
    const rect = image.getBoundingClientRect()
    return rect.width <= viewport.clientWidth && rect.height <= viewport.clientHeight
  }), { timeout: 30_000 }).toBe(true)
  await expect(page.locator('[data-testid^="attention-"]').first()).toBeVisible()
  await expect(page.locator('[data-testid="xlsx-panel"] tbody tr').first()).toBeVisible()
  await page.screenshot({
    path: path.join(ROOT, 'benchmarks/high_visuals/production-high-review.png'), fullPage: true,
  })

  await page.locator('[data-testid="analytics-nav"]').click()
  await expect(page.locator('[data-testid="analytics-view"]')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator(
    '[data-testid="numeric-chart"], [data-testid="categorical-chart"]'
  ).first()).toBeVisible()
  await page.screenshot({
    path: path.join(ROOT, 'benchmarks/high_visuals/production-high-analytics.png'), fullPage: true,
  })

  await page.goto(`${PROD}/dashboard`)
  const lowRow = page.locator('[data-testid^="job-row-"]').filter({ hasText: 'Low · standard' }).first()
  await expect(lowRow).toBeVisible({ timeout: 30_000 })
  await lowRow.click()
  await expect(page.locator('[data-testid="review-content"]')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('[data-testid="review-summary"]')).toHaveCount(0)
  await expect(page.locator('[data-testid^="attention-"]')).toHaveCount(0)
  await expect(page.locator('[data-testid^="ecology-overlay-"]')).toHaveCount(0)
  await page.locator('[data-testid="analytics-nav"]').click()
  await expect(page).toHaveURL(/\/review\//)
})
