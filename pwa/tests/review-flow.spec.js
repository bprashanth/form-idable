import { test, expect } from '@playwright/test'
import * as XLSX from 'xlsx'

const JOB_ID = '5092d717-0aab-4ac8-8c8d-029318822b28'
const workbook = XLSX.utils.book_new()
for (let page = 1; page <= 3; page++) {
  XLSX.utils.book_append_sheet(
    workbook,
    XLSX.utils.aoa_to_sheet([[`Page ${page} workbook marker`], ['value', page]]),
    `page${page}`,
  )
}
const XLSX_FIXTURE = XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' })
const IMAGE_FIXTURE = `
  <svg xmlns="http://www.w3.org/2000/svg" width="800" height="1100" viewBox="0 0 800 1100">
    <rect width="800" height="1100" fill="#fffdf8"/>
    <rect x="70" y="80" width="660" height="900" fill="none" stroke="#58636f" stroke-width="3"/>
    <path d="M70 210h660M70 360h660M70 510h660M70 660h660M70 810h660M250 210v600M480 210v600" stroke="#87919b" stroke-width="2"/>
    <text x="90" y="150" font-family="sans-serif" font-size="32">Local review fixture</text>
  </svg>`

// Reset mock server state before each test so mutations don't leak between tests
test.beforeEach(async ({ request, page }) => {
  await request.get('/api/dev/reset')
  await page.route('**/api/jobs/*/manifest', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      pages: [1, 2, 3].map(number => ({
        page: number,
        render: `page_${number}.png`,
        crops: [{ file: `crop_${number}.png`, bbox: [0.08, 0.08, 0.92, 0.42], rows: '1:5', note: `page ${number} fixture` }],
      })),
    }),
  }))
  await page.route('**/api/jobs/*/xlsx', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ url: '/test-output.xlsx', filename: 'output.xlsx' }),
  }))
  await page.route('**/test-output.xlsx', route => route.fulfill({
    status: 200, contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    body: XLSX_FIXTURE,
  }))
  await page.route('**/api/jobs/*/pages/*', route => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify({ url: '/test-page.svg' }),
  }))
  await page.route('**/api/jobs/*/crops/*', route => route.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify({ url: '/test-page.svg' }),
  }))
  await page.route('**/test-page.svg', route => route.fulfill({
    status: 200, contentType: 'image/svg+xml', body: IMAGE_FIXTURE,
  }))
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
    await expect(firstRow).toContainText('Low · standard')
  })

  test('high effort is explicit per upload and visible on the queued job', async ({ page }) => {
    let extractBody
    page.on('request', request => {
      if (request.method() === 'POST' && request.url().endsWith('/vision/extract')) {
        extractBody = request.postDataJSON()
      }
    })
    await page.goto('/dashboard')
    await page.locator('[data-testid="add-forms-btn"]').click()
    await page.locator('[data-testid="effort-high"]').click()
    await page.locator('[data-testid="modal-file-input"]').setInputFiles({
      name: 'HighForm.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 high'),
    })
    await page.locator('[data-testid="upload-submit-btn"]').click()
    const firstRow = page.locator('[data-testid^="job-row-"]').first()
    await expect(firstRow).toContainText('HighForm.pdf')
    await expect(firstRow).toContainText('High · dual reader')
    expect(extractBody.effort).toBe('high')
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
    await expect(page.locator('[data-testid="xlsx-panel"]')).toContainText('Page 1 workbook marker')
    await page.locator('button:has(span.material-symbols-outlined:text("chevron_right"))').click()
    await expect(page.locator('[data-testid="page-img-2"]')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('[data-testid="xlsx-panel"]')).toContainText('Page 2 workbook marker')
    await expect(page.locator('[data-testid="xlsx-panel"]')).not.toContainText('Page 1 workbook marker')
  })

  test('low effort keeps the original review surface', async ({ page }) => {
    await expect(page.locator('[data-testid="review-summary"]')).toHaveCount(0)
    await expect(page.locator('[data-testid^="attention-"]')).toHaveCount(0)
    await expect(page.locator('[data-testid^="ecology-overlay-"]')).toHaveCount(0)
    await page.locator('[data-testid="analytics-nav"]').click()
    await expect(page).toHaveURL(`/review/${JOB_ID}`)
  })
})

test.describe('Focused review queues', () => {
  test.beforeEach(async ({ page }) => {
    await page.route(`**/api/jobs/${JOB_ID}/review-manifest`, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          version: 'formidable-review-v1',
          policy: {
            literal_transcription_is_immutable: true,
            peer_readers_select_review_regions_not_replacements: true,
            ecology_suggestions_are_separate: true,
          },
          summary: {
            target_cells_including_blanks: 120,
            transcription_review_cells: 1,
            ecology_findings: 1,
          },
          cells: [{
            id: 'p1:r1_c1', page: 1, xlsx_row: 2, xlsx_column: 2,
            bbox: [0.2, 0.3, 0.3, 0.35], presented_value: '8.4',
          }],
          views: {
            transcription_attention: [{
              cell_id: 'p1:r1_c1', page: 1, bbox: [0.2, 0.3, 0.3, 0.35],
              priority: 'high', reason: 'literal readers disagree',
              presented_value: '8.4', alternatives: ['6.4'],
            }],
            ecology_anomalies: [{
              finding_id: 1, code: 'within_form_numeric_outlier', severity: 'medium',
              message: '150 is a robust within-column outlier', label: 'Soil temperature',
              observed: '150', median: 8.2, mad: 1.1,
              proposed_value: null, bbox: [0.54, 0.3, 0.64, 0.35],
              xlsx_row: 2, xlsx_column: 1,
              location: { page: 1, bbox: [0.54, 0.3, 0.64, 0.35], xlsx_row: 2, xlsx_column: 1 },
            }],
          },
        }),
      })
    })
    await page.goto(`/review/${JOB_ID}`)
    await page.locator('[data-testid="page-img-1"]').waitFor({ state: 'visible', timeout: 15_000 })
  })

  test('keeps transcription and ecology findings in separate views', async ({ page }) => {
    await expect(page.locator('[data-testid="review-summary"]')).toBeVisible()
    await expect(page.locator('[data-testid^="attention-"]').first()).toBeVisible()
    await expect(page.locator('[data-testid^="ecology-overlay-"]').first()).toBeVisible()

    await page.locator('[data-testid="review-mode-attention"]').click()
    await expect(page.locator('[data-testid="attention-queue"]')).toContainText('literal readers disagree')
    await expect(page.locator('[data-testid^="attention-"]').first()).toBeVisible()
    if (process.env.FORMIDABLE_SCREENSHOT) {
      await page.screenshot({ path: process.env.FORMIDABLE_SCREENSHOT, fullPage: true })
    }

    await page.locator('[data-testid="review-mode-ecology"]').click()
    await expect(page.locator('[data-testid="ecology-queue"]')).toContainText('robust within-column outlier')
    await expect(page.locator('[data-testid="ecology-queue"]')).toContainText('Flag only—no value was changed.')
  })

  test('opens the exact attention bbox for literal correction', async ({ page }) => {
    await page.locator('[data-testid="review-mode-attention"]').click()
    await page.locator('[data-testid="attention-queue"] button').first().click()
    await expect(page.locator('[data-testid="review-modal"]')).toBeVisible()
    await expect(page.locator('[data-testid="modal-zoom-canvas"]')).toBeVisible()
    await expect(page.locator('[data-testid="review-modal"]')).toContainText('literal readers disagree')
    await expect(page.locator('[data-testid="review-modal"] input')).toHaveCount(2)
  })

  test('analytics shows distributions without editing controls', async ({ page }) => {
    await page.route(`**/api/jobs/${JOB_ID}/analytics`, route => route.fulfill({
      status: 200, contentType: 'application/json', body: JSON.stringify({
        version: 'formidable-analytics-v1',
        summary: { pages: 3, cells: 120, filled: 80, blank: 40, completeness: 0.667,
          disagreements: 1, ecology_findings: 1 },
        pages: [{ page: 1, cells: 40, filled: 30, blank: 10, disagreements: 1, ecology_flags: 1 }],
        charts: [
          { type: 'numeric', label: 'Soil temperature', n: 8, min: 4, q1: 6, median: 8,
            q3: 10, max: 150, histogram: [{ x0: 4, x1: 20, count: 7 }, { x0: 20, x1: 150, count: 1 }] },
          { type: 'categorical', label: 'Phenophase', n: 4,
            values: [{ label: 'leaf flush', count: 3 }, { label: 'flower', count: 1 }] },
        ],
        ecology_findings: [{ code: 'within_form_numeric_outlier', severity: 'medium',
          label: 'Soil temperature', observed: 150, message: 'Investigate this tail', location: { page: 1 } }],
      }),
    }))
    await page.locator('[data-testid="analytics-nav"]').click()
    await expect(page).toHaveURL(`/analytics/${JOB_ID}`)
    await expect(page.locator('[data-testid="analytics-view"]')).toBeVisible()
    await expect(page.locator('[data-testid="numeric-chart"]')).toContainText('Soil temperature')
    await expect(page.locator('[data-testid="categorical-chart"]')).toContainText('Phenophase')
    await expect(page.getByText('SUBMIT REVIEW')).toHaveCount(0)
    if (process.env.FORMIDABLE_ANALYTICS_SCREENSHOT) {
      await page.screenshot({ path: process.env.FORMIDABLE_ANALYTICS_SCREENSHOT, fullPage: true })
    }
  })
})
