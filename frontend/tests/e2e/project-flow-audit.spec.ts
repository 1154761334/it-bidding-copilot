import { expect, test } from '@playwright/test';

test.describe('project flow audit', () => {
  test('enterprise basics page can save current profile safely', async ({ page }) => {
    await page.goto('/#/profile/basics');
    await expect(page.getByText('企业主体信息维护', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: '保存基础信息' }).click();
    await expect(page.getByText('企业基础信息已更新', { exact: true })).toBeVisible();
  });

  test('rfp page shows analysis quality report', async ({ page }) => {
    await page.goto('/#/rfp');
    await expect(page.getByText('RFP 标书智能解构', { exact: true })).toBeVisible();
    await expect(page.getByText(/采购文件识别(通过质量校验|需要人工复核)/)).toBeVisible();
    await expect(page.getByText(/要求数 \d+/)).toBeVisible();
  });

  test('rfp page exposes project confirmation state', async ({ page }) => {
    await page.goto('/#/rfp');
    await expect(
      page.getByText('已确认建档', { exact: true })
        .or(page.getByRole('button', { name: '确认分析结果' }))
        .or(page.getByRole('button', { name: '进入偏离矩阵确认' })),
    ).toBeVisible();
  });

  test('deviation matrix supports saving current matrix', async ({ page }) => {
    await page.goto('/#/deviation');
    await expect(page.getByText('点对点参数偏离矩阵', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: '保存矩阵' })).toBeVisible();
    await page.getByRole('button', { name: '保存矩阵' }).click();
    await expect(page.getByText(/已保存 \d+ 条偏离矩阵应答/)).toBeVisible();
  });

  test('bidding hall loads outline and generation controls', async ({ page }) => {
    await page.goto('/#/bidding');
    await expect(page.getByText('标书大纲', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: '整项目自动续写' })).toBeVisible();
    await expect(page.getByRole('button', { name: '重试未完成章节' })).toBeVisible();
    await expect(page.getByRole('button', { name: /触发智能补全|重试当前章节/ })).toBeVisible();
  });

  test('bidding hall exposes project materials confirmation step', async ({ page }) => {
    await page.goto('/#/bidding');
    await expect(page.getByText('起草前素材确认', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: '智能推荐勾选' })).toBeVisible();
    await expect(page.getByRole('button', { name: '确认素材后开始起草' })).toBeVisible();
  });

  test('bidding hall exposes markdown editor and save action', async ({ page }) => {
    await page.goto('/#/bidding');
    await expect(page.getByTestId('bidding-markdown-editor')).toBeVisible();
    await expect(page.getByRole('button', { name: '保存改稿' })).toBeVisible();
  });

  test('bidding hall can save edited markdown content', async ({ page }) => {
    await page.goto('/#/bidding');
    const editor = page.getByTestId('bidding-markdown-editor');
    await expect(editor).toBeVisible();

    const uniqueLine = `\n\n自动化改稿校验 ${Date.now()}`;
    await editor.fill(`# 自动化改稿测试${uniqueLine}`);
    const saveResponsePromise = page.waitForResponse((response) =>
      response.url().includes('/api/v1/bid/draft/') &&
      response.url().includes('/content') &&
      response.request().method() === 'PUT',
    );
    await page.getByRole('button', { name: '保存改稿' }).click();
    await expect.poll(async () => (await saveResponsePromise).status()).toBe(200);

    await expect(editor).toHaveValue(new RegExp(`自动化改稿校验 \\d+`));
  });

  test('audit page can fetch review records', async ({ page }) => {
    await page.goto('/#/audit');
    await expect(page.getByText('红队终审', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: /开始终审|正在执行终审/ }).click();
    const visibleSignals = [
      page.getByRole('heading', { name: '审标记录' }),
      page.getByRole('heading', { name: '发现关键风险' }),
      page.getByRole('heading', { name: '章节尚未收口' }),
      page.getByText('终审通过', { exact: true }),
    ];
    let matched = false;
    for (const locator of visibleSignals) {
      if (await locator.count()) {
        await expect(locator.first()).toBeVisible();
        matched = true;
        break;
      }
    }
    expect(matched).toBeTruthy();
  });

  test('review page blocks export when readiness is not met', async ({ page }) => {
    await page.goto('/#/review');
    await expect(page.getByText('标书终审与离线导出', { exact: true })).toBeVisible();
    await expect(page.getByText(/导出条件(已满足|未满足)/)).toBeVisible();
    const exportButton = page.getByRole('button', { name: /终审导出|download/i }).last();
    await expect(exportButton).toBeDisabled();
  });

  test('enterprise asset page shows latest ingest batch summary', async ({ page }) => {
    await page.goto('/#/profile');
    await expect(page.getByText('企业建库确认', { exact: true })).toBeVisible();
    await expect(page.getByText('本轮新入库资产待确认', { exact: true })).toBeVisible();
  });
});
