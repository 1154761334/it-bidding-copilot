import { expect, test } from '@playwright/test';

test.describe('Enterprise Asset Center', () => {
  test('can locate and delete a temporary certificate asset', async ({ page, request }) => {
    const uniqueName = `PW-临时证书-${Date.now()}`;

    const createResponse = await request.post('/api/v1/enterprise/assets/certificate', {
      data: {
        raw_name: uniqueName,
        cert_type: 'Playwright测试',
        cert_level: '临时',
        expiry_date: '2026-12-31',
        certification_scope: 'Playwright 自动化临时测试资产',
      },
    });
    expect(createResponse.ok()).toBeTruthy();

    await page.goto('/#/profile');
    await expect(page.getByRole('heading', { name: '企业资产中心' })).toBeVisible();

    const searchInput = page.getByPlaceholder('搜索证书名、项目名、人员角色、文件名');
    await searchInput.clear();
    await searchInput.fill(uniqueName);

    const rowTitle = page.getByText(uniqueName, { exact: true }).first();
    await expect(rowTitle).toBeVisible({ timeout: 15000 });
    await rowTitle.click();

    await page.getByRole('button', { name: '编辑', exact: true }).click();
    await expect(page.getByText('编辑当前资产')).toBeVisible();
    await page.getByTestId('enterprise-delete-asset-submit').click();

    await expect(rowTitle).not.toBeVisible();
    await expect(page.getByText('当前筛选下没有找到资产。可以切换分类、手动新增或重新上传材料。')).toBeVisible();
  });
});
