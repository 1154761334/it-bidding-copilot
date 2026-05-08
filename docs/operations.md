# 运行维护

## 日常启动

```bash
docker compose up -d
cd backend && source venv/bin/activate && uvicorn src.main:app --host 127.0.0.1 --port 8000
cd frontend && pnpm dev:spa --host 127.0.0.1
```

打开前端 `/bid` 后先看左侧 API 状态：

- `API: ok` 表示 FastAPI 可访问。
- `Evidence: N items` 表示数据库中可检索证据数量。
- `Projects: N` 表示 `BIDDING_DATA_DIR` 中可加载项目数量。

## 导入证据

默认从 `VAULT_ROOT` 读取：

- `10-Knowledge/Evergreen/商务技术文件.md`
- `10-Knowledge/Evergreen/招标文件案例.md`

试跑：

```bash
cd backend
venv/bin/python -m src.ingest --dry-run
```

正式写入数据库：

```bash
cd backend
venv/bin/python -m src.ingest
```

正式写入会清空现有 evidence items 后重建。执行前确认当前数据库不是需要保留的生产数据。

## 真实案例 Demo

前端点击 `Demo Real Case` 或调用：

```bash
curl -X POST http://127.0.0.1:8000/demo/real-case
```

后端会从 `DEMO_TENDER_PATH` 读取招标文件，创建项目，并依次执行 Plan、Approve、Execute、Review。

## 产物位置

默认输出在：

```text
workspaces/api-projects/<project-id>/
├── project.json
├── sources/
└── artifacts/
    ├── plan.md
    ├── response_matrix.md
    ├── draft.md
    ├── review.md
    ├── handoff.md
    └── evidence_trace.json
```

该目录是运行态数据，默认不提交。

## 生产路由 smoke

开发直连 SPA 使用：

```bash
cd frontend
pnpm run acceptance:bid-smoke:local
```

生产风格 Next 路由需要先运行本地 Next 服务，再捕获登录态：

```bash
cd frontend
pnpm run capture:bid-storage-state:prod
BID_ROUTE_STORAGE_STATE=.auth/bid-route-storage-state.json pnpm run smoke:bid-route:prod
```

`.auth/` 已忽略，不能提交。

## 常见问题

### API not connected

检查：

```bash
curl http://127.0.0.1:8000/health
```

如果前端后端不在默认地址，设置 `NEXT_PUBLIC_BIDDING_API_BASE_URL`。

### evidence_count 为 0

检查数据库是否启动、`DATABASE_URL` 是否匹配 Compose 端口，并运行：

```bash
cd backend
venv/bin/python -m src.ingest --dry-run
venv/bin/python -m src.ingest
```

### Demo 报 Real tender case not found

检查 `VAULT_ROOT` 和 `DEMO_TENDER_PATH`。私有 Vault 默认不提交，需要在本机准备。

### LLM_API_KEY is not configured

这是 legacy LLM workflow 的预期错误。`/bid` 确定性主线和 smoke 不要求 LLM key。需要真实 LLM 时，配置 `LLM_BASE_URL`、`LLM_API_KEY` 和 `LLM_MODEL`。

### Docker Compose 密码

Compose 默认密码只适合本地开发。任何共享环境或生产环境都必须通过 `.env` 覆盖。
