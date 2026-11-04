# guance-rag 检索工程

本目录是已发布政策知识库的只读 Python 检索实现，支持 BM25、dense/hybrid（需相同嵌入空间）、分页原文回读及媒体来源读取。

从仓库根目录执行 `python -m pip install -e "./rag库/检索工程"`。

真实检索需要**单独恢复**的 RAG 数据目录。恢复方法见 [RAG README](../README.md)，数据与模型服务配置均不存于本仓库。

主要入口：`from guance_rag.runtime import RagKnowledgeBase` 和 `from guance_rag.config import RuntimeOptions`，或使用 `guance-rag` 命令行入口。通过 `KB_BACKEND=rag`、`RAG_STORE_PROJECT` 连接 Agent。
