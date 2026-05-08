# 配置说明

## 配置文件

项目提供两个模板：

- `.env.example`：仓库级本地服务、后端和前端公共变量。
- `backend/.env.example`：后端运行时变量，适合从 `backend/` 目录启动服务时复制。

实际密钥写入 `.env` 或 `backend/.env`，不要提交。

`backend/src/config.py` 会按顺序读取：

1. 仓库根目录 `.env`
2. `backend/.env`
3. 系统环境变量

后读取的值覆盖先读取的值。未知变量会被忽略，便于前后端共用一个根 `.env`。

## 后端变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql://bidding_user:bidding_password@localhost:5433/bidding_db` | PostgreSQL/pgvector 连接。 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接，当前不是 `/bid` 强依赖。 |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO legacy 兼容配置。 |
| `MINIO_ACCESS_KEY` | 空 | 不要提交真实值。 |
| `MINIO_SECRET_KEY` | 空 | 不要提交真实值。 |
| `MINIO_SECURE` | `false` | 本地通常为 `false`。 |
| `LLM_BASE_URL` | `https://ark.cn-beijing.volces.com/api/coding/v3` | OpenAI-compatible chat endpoint。 |
| `LLM_API_KEY` | 空 | legacy LLM workflow 必需。 |
| `LLM_MODEL` | `kimi-k2.6` | 默认示例模型，可替换成供应商支持的模型。 |
| `EMBEDDING_BASE_URL` | `https://api.siliconflow.cn/v1` | OpenAI-compatible embedding endpoint。 |
| `EMBEDDING_API_KEY` | 空 | 为空时自动使用关键词检索。 |
| `EMBEDDING_MODEL` | `Pro/BAAI/bge-m3` | 默认示例 embedding 模型。 |
| `EMBEDDING_DIM` | `1024` | 需要与数据库向量维度一致。 |
| `REPO_ROOT` | 自动推导 | 仓库根目录，一般不需要设置。 |
| `VAULT_ROOT` | `vault` | 私有知识 Vault 路径，可用绝对路径或仓库相对路径。 |
| `DEMO_TENDER_PATH` | `vault/10-Knowledge/Evergreen/招标文件案例.md` | 真实案例 Demo 招标文件。 |
| `BIDDING_DATA_DIR` | `workspaces/api-projects` | API 项目状态和 Artifact 输出目录。 |

## 前端变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `NEXT_PUBLIC_BIDDING_API_BASE_URL` | `http://localhost:8000` | `/bid` API base URL。 |
| `APP_URL` | 无 | 生产 Next 路由 smoke 需要。 |
| `DATABASE_DRIVER` | 无 | LobeHub 上游生产路由需要。 |
| `AUTH_SECRET` | 无 | 生产登录场景需要，不提交。 |
| `KEY_VAULTS_SECRET` | 无 | 生产登录场景需要，不提交。 |
| `BID_ROUTE_STORAGE_STATE` | `.auth/bid-route-storage-state.json` | Playwright storage state，`.auth/` 已忽略。 |

## Docker Compose 变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `POSTGRES_USER` | `bidding_user` | 本地数据库用户。 |
| `POSTGRES_PASSWORD` | `bidding_password` | 本地开发默认密码，生产必须改。 |
| `POSTGRES_DB` | `bidding_db` | 本地数据库名。 |
| `POSTGRES_PORT` | `5433` | 宿主机端口。 |
| `REDIS_PORT` | `6379` | 宿主机端口。 |
| `MINIO_ROOT_USER` | `bidding_minio_user` | 本地 MinIO 用户。 |
| `MINIO_ROOT_PASSWORD` | `bidding_minio_password` | 本地开发默认密码，生产必须改。 |
| `MINIO_API_PORT` | `9000` | MinIO API 端口。 |
| `MINIO_CONSOLE_PORT` | `9001` | MinIO Console 端口。 |

## 模型配置原则

- 文档可记录推荐模型，但代码不得依赖固定模型名。
- `LLM_API_KEY` 缺失时，legacy LLM workflow 应明确报错。
- `/bid` 确定性主线不能因为缺少 LLM key 而无法跑 smoke。
- embedding 调用失败时必须降级到关键词检索。
- 不在仓库中写真实 key、供应商账号、客户材料路径或登录 storage state。
