import { expect, test } from '@playwright/test';

const pages = [
  { path: '/dashboard', heading: '欢迎回来，管理员' },
  { path: '/profile', heading: '企业资产中心' },
  { path: '/profile/basics', heading: '企业主体信息维护' },
  { path: '/rfp', heading: 'RFP 标书智能解构' },
  { path: '/deviation', heading: '点对点参数偏离矩阵' },
  { path: '/bidding', heading: '标书大纲' },
  { path: '/audit', heading: '红队终审' },
  { path: '/review', heading: '标书终审与离线导出' },
];

test.describe('site smoke', () => {
  for (const pageConfig of pages) {
    test(`loads ${pageConfig.path}`, async ({ page }) => {
      await page.goto(`/#${pageConfig.path}`);
      await expect(page.getByText(pageConfig.heading, { exact: true }).first()).toBeVisible();
      await expect(page.getByText('页面正在建设中...')).toHaveCount(0);
    });
  }

  test('dashboard quick action navigates to rfp page', async ({ page }) => {
    await page.goto('/#/dashboard');
    await page.getByRole('button', { name: '解析新标书' }).click();
    await expect(page).toHaveURL(/#\/rfp$/);
    await expect(page.getByText('RFP 标书智能解构', { exact: true })).toBeVisible();
  });
});
