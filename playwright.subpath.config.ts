import { defineConfig } from '@playwright/test';
import base from './playwright.config';

if (!process.env.SMOKE_BASE_URL) throw new Error('Run npm run test:subpath to start an isolated artifact server');
export default defineConfig({
  ...base,
  webServer: undefined,
  outputDir: 'test-results/subpath',
  reporter: [['list'], ['html', { outputFolder: 'playwright-report/subpath', open: 'never' }]],
});
