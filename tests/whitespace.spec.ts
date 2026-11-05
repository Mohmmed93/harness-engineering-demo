import {test,expect} from '@playwright/test';
test('surrounding and whitespace-only searches preserve filters', async({page})=>{
 await page.goto('./');
 await page.getByLabel('Search tickets').fill('report');
 await expect(page.locator('.ticket')).toHaveCount(1);
 await page.getByLabel('Search tickets').fill(' report ');
 await expect(page.locator('.ticket')).toHaveCount(1);
 await page.getByLabel('Search tickets').fill('   ');
 await expect(page.locator('.ticket')).toHaveCount(6);
 await page.getByLabel('Filter by status').selectOption('Open');
 await page.getByLabel('Filter by priority').selectOption('High');
 await page.getByLabel('Search tickets').fill(' report ');
 await expect(page.locator('.ticket')).toHaveCount(1);
 await page.getByLabel('Search tickets').fill('   ');
 await expect(page.locator('.ticket')).toHaveCount(1);
 await expect(page.getByLabel('Filter by status')).toHaveValue('Open');
 await expect(page.getByLabel('Filter by priority')).toHaveValue('High');
});
