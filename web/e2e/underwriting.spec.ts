import { test, expect, type Page } from '@playwright/test'

/* The demo signs a real underwriter in and drops them on the portfolio. These
 * tests lock the behaviour that matters for the demo:
 *   1. the sign-in gate offers every persona,
 *   2. an underwriter lands on the WHOLE 200-case plane (not their 6-case queue
 *      collapsed into one flat band — the regression we just fixed),
 *   3. "My queue" still narrows the plane and the list to that desk, and
 *   4. a case can be opened and a decision recorded end to end.
 * Maria Rivera is the senior desk — the persona whose queue is smallest, so if
 * the plane ever silently falls back to "mine" again, test 2 goes red. */

const SENIOR = 'Maria Rivera'

async function signInAs(page: Page, name: string) {
  await page.getByRole('button', { name: new RegExp(name) }).first().click()
  await page.getByRole('button', { name: new RegExp(`Sign in as ${name}`) }).click()
  // the portfolio is up once the plane is mounted
  await expect(page.locator('.plane__svg')).toBeVisible()
}

test.beforeEach(async ({ page }) => {
  await page.goto('/')
})

test('sign-in gate offers every persona', async ({ page }) => {
  for (const name of ['Evan Wong', 'Dana Park', 'Nadia Sethi', 'Marcus Vale', 'Priya Anand', SENIOR]) {
    await expect(page.getByRole('button', { name: new RegExp(name) })).toBeVisible()
  }
})

async function signInPlain(page: Page, name: string) {
  await page.getByRole('button', { name: new RegExp(name) }).first().click()
  await page.getByRole('button', { name: new RegExp(`Sign in as ${name}`) }).click()
}

test('the executive lands on the money view', async ({ page }) => {
  await signInPlain(page, 'Marcus Vale')
  await expect(page.getByRole('heading', { name: /as money/i })).toBeVisible()
  await expect(page.locator('.exposure__figure')).toBeVisible()
  await expect(page.locator('.mixbar__seg')).toHaveCount(3)
})

test('the admin lands on the audit trail', async ({ page }) => {
  await signInPlain(page, 'Priya Anand')
  await expect(page.getByRole('heading', { name: 'Recorded decisions' })).toBeVisible()
})

test('an underwriter lands on the full 200-case plane', async ({ page }) => {
  await signInAs(page, SENIOR)
  // every case is plotted, not just the signed-in desk's queue
  await expect(page.locator('.plane__dot')).toHaveCount(200)
  // "All" is the active filter on landing
  await expect(page.getByRole('button', { name: /^All/ })).toHaveAttribute('aria-pressed', 'true')
})

test('"My queue" narrows the plane and the list to the senior desk', async ({ page }) => {
  await signInAs(page, SENIOR)
  await page.getByRole('button', { name: /My queue/ }).click()
  await expect(page).toHaveURL(/filter=mine/)
  await expect(page.locator('.plane__dot')).toHaveCount(6)
  await expect(page.locator('.queue__row')).toHaveCount(6)
})

test('an underwriter can open a case and record a decision', async ({ page }) => {
  await signInAs(page, SENIOR)
  await page.locator('.queue__row').first().click()

  const panel = page.locator('.decide')
  await expect(panel.getByRole('heading', { name: 'Record your decision' })).toBeVisible()
  await panel.getByRole('radio', { name: 'Approve' }).click()
  await panel
    .getByPlaceholder('What did you conclude, and on what evidence?')
    .fill('Verified income and coverage; risk within appetite.')
  await panel.getByRole('button', { name: 'Record decision' }).click()

  await expect(panel.getByText('Decision recorded.')).toBeVisible()
  // the recorded decision reads back into the audit trail
  await expect(panel.locator('.decide__trail .decide__entry')).toHaveCount(1)
})
