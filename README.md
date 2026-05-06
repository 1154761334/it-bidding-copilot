# bid-stack

统一的本地开发与运行入口目录。

这里把三类东西放在一起管理：
- `Bidding-agent/`：投标域产品层
- `obsidian_vault_pipeline/`：OVP fork，本地知识层上游
- `workspaces/`：实际项目工作区

## 目录结构

```text
/root/it-bidding-copilot/
├── Bidding-agent/
├── obsidian_vault_pipeline/
├── workspaces/
└── bin/
```

## 快速开始

### 1. 检查环境
```bash
bash /root/it-bidding-copilot/bin/check-stack.sh
```

### 2. 创建一个新工作区
```bash
bash /root/it-bidding-copilot/bin/new-workspace.sh my-bid-project project-001
```

这会自动：
- 初始化 OVP 原生 workspace
- 创建当前项目输入文件夹
- 在 workspace 根目录复制 `.env` 模板

### 3. 编辑 OVP vault `.env`
默认位置：
```text
/root/it-bidding-copilot/workspaces/my-bid-project/bid-vault/.env
/root/it-bidding-copilot/workspaces/my-bid-project/.env
```

### 4. 检查 OVP 配置
```bash
bash /root/it-bidding-copilot/bin/check-vault.sh my-bid-project
```

### 5. 启动投标经理
```bash
bash /root/it-bidding-copilot/bin/start-bid-manager.sh my-bid-project
```

## 材料放置约定

当前项目输入：
- 招标文件、补遗、清单、项目附件
  放到：
  `workspaces/<workspace>/50-Inbox/01-Raw/current-tender/<project-id>/tender/`
- 当前项目专属我方补充材料
  放到：
  `workspaces/<workspace>/50-Inbox/01-Raw/current-tender/<project-id>/company-inputs/`
- 当前项目专属厂商材料
  放到：
  `workspaces/<workspace>/50-Inbox/01-Raw/current-tender/<project-id>/vendor-inputs/`

长期可复用知识：
- 历史标书
  放到：
  `workspaces/<workspace>/50-Inbox/01-Raw/historical-bid/`
- 公司资质
  放到：
  `workspaces/<workspace>/50-Inbox/01-Raw/company-credentials/`
- 厂商长期材料
  放到：
  `workspaces/<workspace>/50-Inbox/01-Raw/vendor-solutions/`

## 顶层约定

- `/root/it-bidding-copilot/` 根目录尽量只放：
  - 两个代码仓库
  - `workspaces/`
  - `bin/`
- 不建议把真实项目文档长期直接堆在根目录。
- 若需要临时整理 `.docx`，优先使用：
  `bash /root/it-bidding-copilot/Bidding-agent/scripts/convert-docx.sh ...`

## 常用路径

- 产品仓库：
  `/root/it-bidding-copilot/Bidding-agent`
- OVP fork：
  `/root/it-bidding-copilot/obsidian_vault_pipeline`
- 默认测试工作区：
  `/root/it-bidding-copilot/workspaces/my-bid-project`
- 顶层脚本：
  `/root/it-bidding-copilot/bin`
