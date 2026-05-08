# 开发指南

## 推荐开发顺序

1. 更新后端 API 或 Artifact 合约。
2. 更新 `frontend/src/services/bidding.ts` 类型。
3. 更新 Zustand store 和对应 Tab UI。
4. 更新 smoke/acceptance 脚本。
5. 更新 README、`docs/`、子目录 README 和 `DEV_LOG.md`。

这样可以避免 UI 先行导致合约不清。

## 本地环境

```bash
cp .env.example .env
cp backend/.env.example backend/.env
docker compose up -d
```

后端：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

前端：

```bash
cd frontend
pnpm install
pnpm dev:spa --host 127.0.0.1
```

## 后端开发边界

- `api_workbench.py` 是当前 `/bid` 主线，不要把它和 legacy LangGraph 状态机强耦合。
- `workflow.py` 可以继续演进 LLM 路径，但验收不能只依赖供应商 key。
- `evidence.py` 必须保留关键词 fallback。
- `config.py` 是路径和模型配置唯一入口，避免在业务代码中写绝对路径。
- 新 Artifact 应同步补充 `docs/api-and-artifacts.md` 和前端默认 Artifact 排序。

## 前端开发边界

- `/bid` 定制代码集中在 `src/features/Bidding`、`src/store/bidding`、`src/services/bidding.ts` 和 `scripts/bidding`。
- vendored LobeHub 上游代码不要做无关格式化。
- API shape 改动必须先更新 TypeScript interface。
- 生产路由登录态只能通过 `.auth/` 保存，不能提交。
- `frontend/README.upstream.md` 保留上游说明，`frontend/README.md` 只描述本项目维护入口。

## 验收分层

基础检查：

```bash
git diff --check -- . ':(exclude)frontend'
docker compose config
backend/venv/bin/python -m py_compile eval_bid_assistant.py backend/src/config.py backend/src/main.py backend/src/api_workbench.py backend/src/ingest.py backend/src/llm.py backend/src/workflow.py
```

后端行为：

```bash
backend/venv/bin/python eval_bid_assistant.py
cd backend && venv/bin/python -m src.ingest --dry-run
cd backend && venv/bin/python tests/api_smoke.py
```

前端行为：

```bash
cd frontend
pnpm run type-check
pnpm run build
pnpm run acceptance:bid-smoke:preflight
pnpm run acceptance:bid-smoke:local
```

## Commit 准则

- 一个提交应对应一组可解释的产品或维护变更。
- 不提交 `.env`、Vault 私有材料、项目运行态、浏览器 storage state、依赖目录和构建产物。
- 如果工作树已有用户改动，先确认范围，避免 `git add -A` 把不相关内容带入。
- 更新文档时记录当前开发进度和已知阻塞。
