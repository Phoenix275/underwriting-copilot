import { defineConfig, devices } from '@playwright/test'

/* End-to-end tests run against the SNAPSHOT build — VITE_API_URL is forced
 * empty by `.env.snapshot`, so the app takes its localStorage decision path and
 * needs no running API. That is exactly the artifact that ships to Cloudflare
 * Pages and GitHub Pages, so these tests exercise what users actually get. A dedicated
 * port keeps this independent of any dev server already running on 5173. */
const PORT = 4321

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list']],
  use: {
    baseURL: `http://localhost:${PORT}`,
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'desktop-chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chromium', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: `npm run dev -- --mode snapshot --port ${PORT} --strictPort`,
    // Probe with a real HTTP request, not just a bound port: a lingering
    // TIME_WAIT socket from a previous run holds the port without serving, and
    // a port-only check would make Playwright assume that dead socket is the
    // server and skip starting one — every navigation then gets
    // ERR_CONNECTION_REFUSED. The url probe waits for an actual 200.
    url: `http://localhost:${PORT}/`,
    // Always start (and tear down) our own server. Never reuse whatever happens
    // to hold the port, so the run is deterministic locally and in CI.
    reuseExistingServer: false,
    timeout: 120_000,
  },
})
