# 管策智研｜政策智能研究 Agent

本仓库为**源码提交版**：只包含运行项目所需的 Python / TypeScript 源代码、前端静态资源、依赖清单、无密钥配置模板和 README。**不包含政策数据集、索引数据、模型权重、训练/评测文件、真实 API 密钥、运行日志和数据库。**

## 项目代码

- `agent/`：政策研究 Agent，执行研究准备、检索决策、引文核验、结果组织及多轮任务。
- `rag库/检索工程/`：检索已发布政策知识库的 Python 后端。
- `rag库/restore_delivery.py`：独立知识库数据包的安全恢复工具。
- `web/backend/`：FastAPI 服务，提供政策问答、文献目录、**Word / Excel 导出**。
- `web/frontend/`：React / Vite 页面，研究答案下方可分别导出 DOCX、XLSX。

## 环境

Python **3.11+**、Node.js **22+**。项目还需要独立配置**有授权的模型服务**和**RAG 运行数据**，它们不随源码提交。RAG 发布库可由有权访问者从[原工程 Release](https://github.com/SKD-Agent-Frontier/guance-policy-intelligence/releases/tag/rag-v0.4.0-data-20261024-r1)获取；见 [RAG 使用与恢复说明](rag库/README.md)。

## 安装

在仓库根目录执行：

```powershell
python -m pip install -e "./agent"
python -m pip install -e "./rag库/检索工程"
python -m pip install -r "./web/backend/requirements.txt"
cd web/frontend
npm ci
```

按 [Agent 配置模板](agent/.env.example) 设置模型和知识库环境，**不要提交真实密钥**。可通过 `GUANCE_ENV_FILE` 选择本机私有配置文件。

## 启动

终端 1，进入 `web/backend`：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

终端 2，进入 `web/frontend`：

```powershell
npm run dev
```

浏览器打开 Vite 输出的本机页面。后端默认端口 8000；前端缺省连接 `http://127.0.0.1:8000`。

## 导出

研究结果下方的按钮支持 Word（保留研究结论、事实及出处）和 Excel（研究结果、核验事实、文献出处、结构化研究四类工作表）。导出文件仅在内存中生成并返回，不会写入仓库或后端磁盘。不导出模型密钥、工具日志或内部配置。
