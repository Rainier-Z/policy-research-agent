# Agent 运行说明

政策研究 Agent 源码位于 `src/guance_agent/`，包括任务分解、受控检索、证据核验、研究报告及会话记忆。模型 Prompt 位于 `src/guance_agent/prompts/`，属于运行必要资源。

从仓库根目录安装：

```powershell
python -m pip install -e "./agent"
python -m pip install -e "./rag库/检索工程"
```

请复制 `agent/.env.example` 为**本机私有环境配置**，设置：

```dotenv
LLM_BASE_URL=<your-openai-compatible-api-url>
LLM_API_KEY=<your-private-key>
LLM_MODEL=<authorized-model>
KB_BACKEND=rag
RAG_STORE_PROJECT=<absolute-path-to-restored-rag-runtime>
RAG_MODE=bm25
```

设置 `GUANCE_ENV_FILE` 指向本机配置，或使用同名环境变量。实际密钥和模型权重不包含在此仓库中。

Web 后端通过 `guance_agent.main.submit` 接入 Agent。完整服务启动方式见 [Web 后端 README](../web/backend/README.md)。本提交不附带演示知识库、训练集或历史研发资料。
