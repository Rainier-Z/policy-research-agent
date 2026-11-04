# RAG 检索与运行数据说明

本目录只保留**运行已建政策知识库所需的检索源码**、无凭据恢复工具和本 README；不包含原始语料、索引、OCR 批次、向量缓存或模型权重。

## 检索工程

在仓库根目录安装：

```powershell
python -m pip install -e "./rag库/检索工程"
```

Python 包为 `guance_rag`，使用 `RuntimeOptions(store_project=Path(...), mode="bm25")` 和 `RagKnowledgeBase` 调用；应用侧通过 `KB_BACKEND=rag`、`RAG_STORE_PROJECT` 连接。

## 外部数据恢复

系统**不能仅凭源码运行真实知识库检索**。具有权限的使用者可从[原项目 RAG v0.4.0 Release](https://github.com/SKD-Agent-Frontier/guance-policy-intelligence/releases/tag/rag-v0.4.0-data-20261024-r1)下载全部分卷、交付清单及 SHA-256 文件。

恢复命令（PowerShell 示例）：

```powershell
python "rag库/restore_delivery.py" --manifest "<download-dir>/delivery-manifest.json" --destination "<new-runtime-dir>"
```

恢复程序验证分卷、压缩包和内容哈希，拒绝写入已有目录；建议预留足够磁盘空间。恢复完成后，将 Agent 的 `RAG_STORE_PROJECT` 设为 `<new-runtime-dir>`。

BM25 与已有冻结文本、图片的回取不需要重新建库。dense/hybrid 查询可能需要授权访问与原发布版本一致的 embedding 服务；私有接口和密钥不随源码提供。

RAG 检索 API 的细节见 [检索模块 README](检索工程/README.md)。
