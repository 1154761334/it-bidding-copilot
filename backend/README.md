# IT Bidding Copilot Backend

后端是 `/bid` 工作台的 FastAPI 服务，负责招标解析、证据检索、投标 Artifact 生成、Review 和真实案例 Demo。

## 主要模块

| 文件 | 说明 |
| --- | --- |
| `src/config.py` | 环境变量、模型配置、仓库相对路径解析。 |
| `src/main.py` | FastAPI 入口、健康检查、workbench endpoints、legacy workflow endpoints。 |
| `src/api_workbench.py` | 当前 `/bid` 主线，生成 Plan、Execute、Review、Handoff 和 Artifact。 |
| `src/parser.py` | Office/PDF 转 Markdown。 |
| `src/evidence.py` | embedding 检索和关键词 fallback。 |
| `src/ingest.py` | Vault Markdown 切块并写入 Evidence Store。 |
| `src/workflow.py` | legacy LangGraph LLM workflow。 |
| `src/models.py` | SQLAlchemy 数据模型。 |
| `src/storage.py` | MinIO legacy 兼容层。 |

## 启动

```bash
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

从仓库根目录启动 Compose：

```bash
docker compose up -d
```

## 配置

后端读取仓库根目录 `.env` 和 `backend/.env`。路径变量可以使用绝对路径，也可以使用仓库相对路径。

关键变量：

- `DATABASE_URL`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `VAULT_ROOT`
- `DEMO_TENDER_PATH`
- `BIDDING_DATA_DIR`

详细说明见 [`../docs/configuration.md`](../docs/configuration.md)。

## Evidence Store

试跑：

```bash
venv/bin/python -m src.ingest --dry-run
```

写入数据库：

```bash
venv/bin/python -m src.ingest
```

没有 `EMBEDDING_API_KEY` 时会写入文本证据并在检索时使用关键词 fallback。

## 验收

```bash
venv/bin/python -m py_compile ../eval_bid_assistant.py src/config.py src/main.py src/api_workbench.py src/ingest.py src/llm.py src/workflow.py
venv/bin/python ../eval_bid_assistant.py
venv/bin/python -m src.ingest --dry-run
venv/bin/python tests/api_smoke.py
```

## 维护边界

- `/bid` 主线不应强依赖外部 LLM key。
- `api_workbench.py` 的 Artifact 文件名是前后端公共合约。
- `vault/` 和 `workspaces/` 是私有或运行态数据，不提交。
- 所有模型供应商都通过 OpenAI-compatible 配置进入，不在业务逻辑中写死供应商。
