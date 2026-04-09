import { expect, test } from '@playwright/test';

test.describe('settings dialog', () => {
  test('opens runtime capability panel', async ({ page }) => {
    await page.goto('/#/dashboard');
    await page.locator('header').getByRole('button', { name: 'settings' }).click();
    await expect(page.getByRole('heading', { name: '系统核心配置' })).toBeVisible();
    await expect(page.getByText('Runtime Capabilities')).toBeVisible();
    await expect(page.getByText('LLM', { exact: true })).toBeVisible();
    await expect(page.getByText('Embedding', { exact: true })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('heading', { name: '系统核心配置' })).toHaveCount(0);
  });
});
