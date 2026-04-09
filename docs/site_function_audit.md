# 全站功能巡检

## 本轮范围

本轮以真实前端页面为准，对当前主站点做了一次浏览器自动化巡检，覆盖：

1. `/dashboard`
2. `/profile`
3. `/profile/basics`
4. `/rfp`
5. `/deviation`
6. `/bidding`
7. `/audit`
8. `/review`
9. 设置弹窗 `/config/capabilities`

同时补充了企业资产中心的真实 CRUD 用例。

## 已补的浏览器用例

- `frontend/tests/e2e/site-smoke.spec.ts`
- `frontend/tests/e2e/project-flow-audit.spec.ts`
- `frontend/tests/e2e/enterprise-assets.spec.ts`
- `frontend/tests/e2e/settings-dialog.spec.ts`

当前 Playwright 配置已改为串行执行：

- `frontend/playwright.config.ts`

原因：

- 当前所有用例共享同一企业与项目上下文
- 并行执行会污染同一批资产和项目状态，制造假失败

## 本轮发现并修复的问题

### 1. RFP 页面刷新后丢失分析结果

现象：

- `/rfp` 页面只在“本次上传解析成功后”显示 `analysis-check`
- 刷新页面或新开标签后，当前项目虽存在，但页面退回“请上传标书”

修复：

- 新增后端接口 `GET /api/v1/rfp/projects/{project_id}`
- 新增前端 `rfpService.getProjectAnalysis`
- 新增 store 恢复方法 `hydrateProjectAnalysis`
- `RFPAnalysis` 页面在已有 `currentProjectId` 时自动恢复项目分析结果

涉及文件：

- `api/routers/rfp_v2.py`
- `frontend/src/services/api.ts`
- `frontend/src/store/useRfpStore.ts`
- `frontend/src/pages/RFPAnalysis.tsx`

### 2. 偏离矩阵页面错误依赖内存态

现象：

- `/deviation` 页面即使当前项目已有矩阵数据，也会因为 `analysisResult` 为空而显示“暂无偏离矩阵数据”

修复：

- 页面改为以 `currentProjectId` 作为主判断条件
- 项目标题优先显示 `analysisResult.project_name`，否则回退到当前项目上下文

涉及文件：

- `frontend/src/pages/DeviationMatrix.tsx`

### 3. 设置弹窗不支持 Escape 关闭

现象：

- 设置弹窗只能点关闭按钮，键盘 `Escape` 无效

修复：

- `SettingsDialog` 新增全局 `keydown` 监听
- 打开弹窗时支持 `Escape` 关闭

涉及文件：

- `frontend/src/components/layout/SettingsDialog.tsx`

### 4. 前后端旧进程导致页面仍命中旧代码

现象：

- 页面和接口偶发仍落到旧版本进程
- `analysis-confirm`、`latest-ingest-batch` 这类新接口代码已存在，但站点联调时仍返回旧结果

修复：

- 排查端口占用，确认 `:8000` 与 `:20031` 上仍有旧手动进程
- 修复 `start_app.sh` 的 PID 记录错误，避免写入错误 PID 后“重启了但没真正切到新代码”
- 重新以当前代码版本启动后端与前端

涉及文件：

- `start_app.sh`

## 当前巡检结论

### 主链页面

- `Dashboard`：通过
- `企业资产中心`：通过
- `企业主体信息维护`：通过
- `RFP 解析`：通过
- `偏离矩阵`：通过
- `编标大厅`：通过
- `红队终审`：通过
- `终审导出`：通过
- `设置能力面板`：通过

### 可安全执行的关键动作

- 企业基础信息保存：通过
- 企业资产新增/搜索/编辑/删除：通过
- RFP 页面恢复当前项目分析结果：通过
- 偏离矩阵保存：通过
- 编标大厅加载当前大纲与批量生成按钮：通过
- 编标大厅在线编辑并保存当前章节：通过
- 红队终审拉取审标记录：通过
- 终审导出拦截未就绪项目：通过
- 设置弹窗读取运行时能力并支持 `Escape` 关闭：通过

## 当前自动化验证结果

### 前端浏览器巡检

```bash
cd frontend && PLAYWRIGHT_BASE_URL='http://127.0.0.1:20031' npx playwright test
```

结果：

- `22 passed`
- `tests/e2e/project-flow-audit.spec.ts` -> `11 passed`

说明：

- 上述结果为本轮文档所记录的历史巡检结果
- 本次代码核对过程中未重新执行 Playwright，因此不能直接等同于“当前代码再次验证通过”

### 后端回归

```bash
./venv/bin/python -m pytest -q
```

历史文档结果：

- `52 passed`

本次重新核验结果：

- `./venv/bin/python -m pytest -q --maxfail=8` -> `8 failed, 8 passed`
- 失败集中在 `DraftingReviewService` / `drafting_v2` 与 `EnterpriseAssetService`
- 说明当前后端回归基线已经失真，需先修复服务层与测试预期漂移

## 剩余建议

1. 继续补“上传真实采购文件 -> analyze”浏览器用例
2. 继续补“整项目自动续写 -> 章节完成状态变化”浏览器用例
3. 继续补“终审后导出 docx 文件存在性”浏览器用例
4. 对 `/config/capabilities` 当前返回的模型名与文档默认值做一次配置一致性核对
