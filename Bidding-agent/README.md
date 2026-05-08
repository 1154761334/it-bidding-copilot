# Bidding-agent

`Bidding-agent/` 是 IT Bidding Copilot 的可选 Hermes/Obsidian 投标经理技能包。它不是当前 `/bid` Web 工作台的运行时依赖，而是面向长期知识工作流、Obsidian Vault 和 OVP 的扩展层。

当前主产品入口见仓库根目录 `README.md`。本目录保留用于：

- 投标经理 Agent 技能定义
- OVP/Obsidian workspace 模板
- 投标证据、章节、评分项和复核模板
- Hermes 手工验收与 benchmark 脚本

## 定位

这个技能包面向系统集成和 IT 投标项目，强调：

- 单一外部身份：`bid-manager`
- 证据优先的投标生产
- 投标人能力与厂商能力分离
- 当前项目输入与长期可复用知识分离
- 起草前必须先有人确认 outline 和材料边界
- 正式稿不得写入无证据资格声明、无签核商务口径或伪造页码

## 目录

| 路径 | 说明 |
| --- | --- |
| `skills/bid-manager/SKILL.md` | Hermes 主技能入口。 |
| `skills/bid-manager/internal/` | 内部模块提示词和 benchmark prompt。 |
| `docs/` | 架构、部署、工作流、子 agent 和仓库边界说明。 |
| `templates/` | 项目启动、证据检索、评分映射、章节起草、材料装订和复核模板。 |
| `templates/workspace/` | 推荐 workspace 骨架。 |
| `scripts/` | prerequisite check、OVP 安装、workspace 初始化和 benchmark。 |
| `examples/demo-project/` | 脱敏轻量示例。 |

## 推荐栈

```text
IT Bidding Copilot root
├── Bidding-agent/
├── obsidian_vault_pipeline/
└── workspaces/
    └── <workspace>/
        ├── 50-Inbox/
        ├── 10-Knowledge/
        ├── 20-Areas/
        └── 60-Logs/
```

## 安装与初始化

从本目录运行：

```bash
bash scripts/check-prereqs.sh
bash scripts/install-ovp.sh local
bash scripts/init-workspace.sh ../workspaces/my-bid-project
bash scripts/new-project-inbox.sh ../workspaces/my-bid-project project-001
cp templates/ovp-vault.env.example ../workspaces/my-bid-project/.env
```

如果 OVP 不在仓库同级目录，设置：

```bash
OVP_LOCAL_PATH=/path/to/obsidian_vault_pipeline bash scripts/install-ovp.sh local
```

## 工作流

1. 项目文件放入 `50-Inbox/01-Raw/current-tender/<project-id>/`。
2. 投标经理读取项目输入和长期知识。
3. 整理招标要求、材料清单和缺口。
4. 建立评分点、章节和证据映射。
5. 用户确认 outline。
6. 分章节起草。
7. Review 废标风险、评分风险、商务/法务风险和材料装订风险。
8. 交付正式稿和可回流知识。

## 与 `/bid` 工作台的关系

- `/bid` 是当前可验收 Web 产品主线。
- `Bidding-agent/` 是 Hermes/Obsidian 知识工作流方向的可选扩展。
- 两者共享投标领域原则：证据优先、人工确认、材料包分工、正式稿事实可追溯。
- 后续如需融合，应先统一 Artifact 和 evidence trace 合约。

## 安全边界

默认不发布：

- 当前项目输入文件
- 原始招标包
- 导出 `.docx` / `.zip`
- 证书图片和证据附件
- 实验 Vault 和大型知识库

只发布技能、模板、脚本、轻量示例和维护文档。
