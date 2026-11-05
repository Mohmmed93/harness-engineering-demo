import { defineConfig } from '@playwright/test';

const port = process.env.TEST_PORT || '4173';
if (!/^\d{1,5}$/.test(port) || Number(port) < 1024 || Number(port) > 65535) {
  throw new Error('TEST_PORT must be a valid unprivileged port');
}
const localURL = `http://127.0.0.1:${port}`;
const isolated = Boolean(process.env.CI || process.env.HARNESS_VERIFY);

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    baseURL: process.env.SMOKE_BASE_URL || localURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: process.env.SMOKE_BASE_URL ? undefined : {
    command: `npm run dev -- --port ${port} --strictPort`,
    url: localURL,
    reuseExistingServer: !isolated,
  },
});
