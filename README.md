# 管策智研｜政策智能研究 Agent

本仓库是**赛事提交用的精简源码副本**。保留 Agent、已建知识库检索与恢复工具、Web 前后端、必要配置示例和自动化测试；不包含原始语料及历史研发产物。

## 工程入口

| 模块 | 功能 | 入口 |
| --- | --- | --- |
| Agent | 政策问答、要素提取、证据引用与多文献分析 | [agent/README.md](agent/README.md) |
| RAG | 已发布知识库检索、逐字原文及图片回读 | [rag库/检索工程](rag库/检索工程/README.md) |
| RAG 运行数据恢复 | 独立恢复 SQLite、BM25/Qdrant、冻结原文和媒体 | [运行数据交付](rag库/运行数据交付.md) |
| Web 后端 | FastAPI 研究接口与政策目录 | [web/backend/README.md](web/backend/README.md) |
| Web 前端 | 政策研究交互页面 | [web/frontend/README.md](web/frontend/README.md) |

## 数据、安装和启动

本仓库**不包含原始语料库和离线切块工程**；系统使用已建好的 506 篇政策 RAG 发布数据。该数据包由原开发仓库的 [RAG v0.4.0 Release](https://github.com/SKD-Agent-Frontier/guance-policy-intelligence/releases/tag/rag-v0.4.0-data-20261024-r1) 独立提供。请按照 [恢复说明](rag库/运行数据交付.md) 下载全部分卷、校验并恢复，然后设置 `RAG_STORE_PROJECT` 指向恢复后的目录。

从仓库根目录安装 Agent 和真实 RAG 检索依赖：

```powershell
python -m pip install -e './agent[dev]'
python -m pip install -e './rag库/检索工程'
python -m pip install -r web/backend/requirements.txt
```

模型服务地址、密钥和本地运行库路径由环境变量或 `GUANCE_ENV_FILE` 指向的**私有本地配置文件**提供，不能提交到 Git。

后端在 `web/backend` 下运行 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`；前端在 `web/frontend` 下执行 `npm ci`、`npm run dev`。参数说明及依赖条件以各模块 README 为准。

## 测试和限制

GitHub Actions 对 Agent、RAG 检索契约、后端和前端进行离线检查。自动化通过不等于真实校内模型 + 完整训练集的业务验收；提交仓库未宣称已完成所有真实端到端题组。原始数据、训练集和赛事资料通过授权渠道单独管理。
