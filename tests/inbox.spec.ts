import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{await page.goto('./');});
test('search preserves status and priority filters',async({page})=>{
 await page.getByLabel('Filter by status').selectOption('Open');
 await page.getByLabel('Filter by priority').selectOption('High');
 await page.getByLabel('Search tickets').fill('report');
 await expect(page.getByRole('button',{name:/1042/})).toBeVisible();
 await page.getByLabel('Search tickets').clear();
 await expect(page.getByLabel('Filter by status')).toHaveValue('Open');
 await expect(page.getByLabel('Filter by priority')).toHaveValue('High');
 await expect(page.locator('.ticket')).toHaveCount(1);
});
test('failed save leaves original status intact and can recover',async({page})=>{
 await page.getByLabel('Simulate save failure').check();
 await page.getByLabel('Ticket status',{exact:true}).selectOption('Resolved');
 await expect(page.getByRole('status')).toContainText('Save failed');
 await expect(page.getByLabel('Ticket status',{exact:true})).toHaveValue('Open');
 await page.getByLabel('Simulate save failure').uncheck();
 await page.getByLabel('Ticket status',{exact:true}).selectOption('Resolved');
 await expect(page.getByRole('status')).toContainText('saved');
 await expect(page.getByLabel('Ticket status',{exact:true})).toHaveValue('Resolved');
});
test('notes stay with their ticket and reset restores fixtures',async({page})=>{
 await page.getByLabel('Internal note').fill('Reproduced in staging');
 await page.getByRole('button',{name:'Add note',exact:true}).click();
 await expect(page.getByText('Reproduced in staging',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:/1041/}).click();
 await expect(page.getByText('Reproduced in staging',{exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:/Reset demo/}).click();
 await expect(page.getByText('Reproduced in staging',{exact:true})).toHaveCount(0);
});
test('empty results explain how to recover',async({page})=>{
 await page.getByLabel('Search tickets').fill('no-such-ticket');
 await expect(page.getByText('No matching tickets')).toBeVisible();
});
