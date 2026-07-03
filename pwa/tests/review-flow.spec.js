import { test, expect } from '@playwright/test'

const JOB_ID = '5092d717-0aab-4ac8-8c8d-029318822b28'

// Reset mock server state before each test so mutations don't leak between tests
test.beforeEach(async ({ request }) => {
  await request.get('/api/dev/reset')
})

test.describe('Dashboard', () => {
  test('loads with job list', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('[data-testid="submission-log"]')).toBeVisible({ timeout: 10_000 })
    const rows = page.locator(`[data-testid^="job-row-"]`)
    await expect(rows).toHaveCount(5)
  })

  test('map renders', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.locator('[data-testid="map"]')).toBeVisible()
  })

  test('clicking a row navigates to review page', async ({ page }) => {
    await page.goto('/dashboard')
    await page.locator(`[data-testid="job-row-${JOB_ID}"]`).waitFor()
    await page.locator(`[data-testid="job-row-${JOB_ID}"]`).click()
    await expect(page).toHaveURL(`/review/${JOB_ID}`)
  })

  test('delete — trash enters select mode', async ({ page }) => {
    await page.goto('/dashboard')
    await page.locator('[data-testid="submission-log"]').waitFor()

    await page.locator('[data-testid="trash-btn"]').click()
    await expect(page.locator('[data-testid="delete-selected-btn"]')).toBeVisible()
    await expect(page.locator('[data-testid="add-forms-btn"]')).not.toBeVisible()
  })

  test('delete — selecting and deleting removes the row', async ({ page }) => {
    await page.goto('/dashboard')
    await page.locator('[data-testid="submission-log"]').waitFor()

    await page.locator('[data-testid="trash-btn"]').click()
    // Check the first job's checkbox
    await page.locator('[data-testid^="select-"]').first().click()
    await page.locator('[data-testid="delete-selected-btn"]').click()

    // Table now shows 4 rows
    await expect(page.locator('[data-testid^="job-row-"]')).toHaveCount(4)
    // Select mode exits automatically
    await expect(page.locator('[data-testid="trash-btn"]')).toBeVisible()
  })

  test('delete — cancel exits select mode without deleting', async ({ page }) => {
    await page.goto('/dashboard')
    await page.locator('[data-testid="submission-log"]').waitFor()

    await page.locator('[data-testid="trash-btn"]').click()
    await page.locator('[data-testid^="select-"]').first().click()
    await page.locator('button:has-text("Cancel")').click()

    await expect(page.locator('[data-testid^="job-row-"]')).toHaveCount(5)
    await expect(page.locator('[data-testid="trash-btn"]')).toBeVisible()
  })

  test('add forms — uploading a file inserts a queued row', async ({ page }) => {
    await page.goto('/dashboard')
    await page.locator('[data-testid="submission-log"]').waitFor()

    // Open the upload modal
    await page.locator('[data-testid="add-forms-btn"]').click()
    await page.locator('[data-testid="upload-modal"]').waitFor()

    // Select files via the modal's hidden file input
    await page.locator('[data-testid="modal-file-input"]').setInputFiles({
      name:     'TestForm.pdf',
      mimeType: 'application/pdf',
      buffer:   Buffer.from('%PDF-1.4 test'),
    })

    // Submit the modal
    await page.locator('[data-testid="upload-submit-btn"]').click()

    // New row appears immediately (prepended)
    await expect(page.locator('[data-testid^="job-row-"]')).toHaveCount(6, { timeout: 5_000 })
    const firstRow = page.locator('[data-testid^="job-row-"]').first()
    await expect(firstRow).toContainText('TestForm.pdf')
    await expect(firstRow).toContainText('queued')
  })
})

test.describe('Review page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/review/${JOB_ID}`)
    await page.locator('[data-testid="review-content"]').waitFor()
  })

  test('page image renders', async ({ page }) => {
    const img = page.locator('[data-testid="page-img-1"]')
    await expect(img).toBeVisible({ timeout: 15_000 })
  })

  test('crop overlays are present', async ({ page }) => {
    await page.locator('[data-testid="page-img-1"]').waitFor({ state: 'visible', timeout: 15_000 })
    const crops = page.locator('[data-testid^="crop-"]')
    await expect(crops.first()).toBeVisible()
  })

  test('clicking a crop overlay opens the crop modal', async ({ page }) => {
    await page.locator('[data-testid="page-img-1"]').waitFor({ state: 'visible', timeout: 15_000 })
    const firstCrop = page.locator('[data-testid^="crop-"]').first()
    await firstCrop.click()
    await expect(page.locator('[data-testid="review-modal"]')).toBeVisible()
    await expect(page.locator('[data-testid="modal-crop-img"]')).toBeVisible()
  })

  test('pressing Escape closes the modal', async ({ page }) => {
    await page.locator('[data-testid="page-img-1"]').waitFor({ state: 'visible', timeout: 15_000 })
    await page.locator('[data-testid^="crop-"]').first().click()
    await expect(page.locator('[data-testid="review-modal"]')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.locator('[data-testid="review-modal"]')).not.toBeVisible()
  })

  test('clicking outside crop opens zoom modal with canvas', async ({ page }) => {
    const img = page.locator('[data-testid="page-img-1"]')
    await img.waitFor({ state: 'visible', timeout: 15_000 })
    const box = await img.boundingBox()
    // Use locator.click with position to reliably hit the img element.
    // Raw page.mouse.click can fail here because the panning layer's mousedown
    // calls e.preventDefault(), which in Playwright/Chromium can suppress the
    // subsequent click event. Crops on page 1 start at y=7%, so 5% is outside.
    await img.click({ position: { x: Math.floor(box.width * 0.05), y: Math.floor(box.height * 0.05) } })
    await expect(page.locator('[data-testid="review-modal"]')).toBeVisible()
    await expect(page.locator('[data-testid="modal-zoom-canvas"]')).toBeVisible()
  })

  test('page navigation moves to next page', async ({ page }) => {
    await page.locator('[data-testid="page-img-1"]').waitFor({ state: 'visible', timeout: 15_000 })
    await page.locator('button:has(span.material-symbols-outlined:text("chevron_right"))').click()
    await expect(page.locator('[data-testid="page-img-2"]')).toBeVisible({ timeout: 10_000 })
  })
})
