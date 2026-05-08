# IT Bidding Copilot Frontend

本目录是 vendored LobeHub/LobeChat 工作区，包含本项目定制的 `/bid` 投标工作台。上游项目说明保留在 `README.upstream.md`，本文件只描述当前仓库的维护入口。

## 项目定制范围

主要定制文件：

| 路径 | 说明 |
| --- | --- |
| `src/business/client/BusinessDesktopRoutes.tsx` | 注册 `/bid` 业务路由。 |
| `src/features/Bidding/` | 投标工作台 UI，包括 Files、Plan、Execute、Review、Draft、Evidence。 |
| `src/services/bidding.ts` | FastAPI client 和 TypeScript wire types。 |
| `src/store/bidding/` | Zustand 状态管理和 workflow actions。 |
| `scripts/bidding/` | `/bid` smoke、preflight、production storage-state 验收脚本。 |
| `package.json` | 新增 bidding acceptance scripts。 |

除上述定制层外，尽量不要批量格式化或重写 vendored 上游代码。

## 后端连接

默认 API 地址：

```text
http://localhost:8000
```

覆盖方式：

```bash
NEXT_PUBLIC_BIDDING_API_BASE_URL=http://127.0.0.1:8000 pnpm dev:spa --host 127.0.0.1
```

## 本地开发

```bash
pnpm install
pnpm dev:spa --host 127.0.0.1
```

需要后端同时运行：

```bash
cd ../backend
source venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

## 验收

服务无关 preflight：

```bash
pnpm run acceptance:bid-smoke:preflight
```

自动启动临时 FastAPI 和 Vite 的本地 smoke：

```bash
pnpm run acceptance:bid-smoke:local
```

类型检查：

```bash
pnpm run type-check
```

构建：

```bash
pnpm run build
```

## 生产风格路由 smoke

先运行本地 Next 服务，再捕获 storage state：

```bash
pnpm run capture:bid-storage-state:prod
BID_ROUTE_STORAGE_STATE=.auth/bid-route-storage-state.json pnpm run smoke:bid-route:prod
```

`.auth/` 已忽略，不提交浏览器登录态。

## 维护规则

- API 字段变更先改 `src/services/bidding.ts`，再改 store 和 UI。
- Artifact 文件名变更必须同步 `src/store/bidding/index.ts` 的默认排序和 smoke 文档。
- 不提交 `node_modules/`、`.next/`、`public/_spa/`、`.auth/`、`.env.desktop`。
- 上游 README、生态说明和通用 LobeHub 文档不作为本项目主 README 使用。
