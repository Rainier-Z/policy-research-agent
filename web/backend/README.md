# Web Backend（FastAPI）

位于 `web/backend/app/`。提供政策研究接口、已发布 RAG 文献目录、报告导出；不内置语料和模型服务。

在仓库根目录安装：

```powershell
python -m pip install -e "./agent"
python -m pip install -e "./rag库/检索工程"
python -m pip install -r "./web/backend/requirements.txt"
```

私有环境配置可由 `GUANCE_ENV_FILE` 指定。必须提供 `LLM_BASE_URL`、`LLM_API_KEY`、`KB_BACKEND=rag`、`RAG_STORE_PROJECT`。为方便本机联调，默认允许 `http://localhost:5173` 和 `http://127.0.0.1:5173` 的 CORS。

在 `web/backend` 下启动：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 主要接口

- `POST /api/runs`：运行研究任务。
- `POST /api/research/prepare`：准备 / 澄清任务。
- `GET /api/policies`：读取冻结发布目录。
- `POST /api/exports/docx`：导出 Word 报告。
- `POST /api/exports/xlsx`：导出 Excel 研究表格。
- `GET /api/health`、`GET /api/readiness`：服务与资源配置状态。

导出端点仅接收页面当前可见的研究结果字段；输出由 python-docx / XlsxWriter **在内存中**生成。仅已完成的研究允许正式导出；证据不足会在文件中提示。服务器不保留导出文件。

行政区划与政策分类使用已配置的外部或运行时数据；缺少相关映射时部分维度筛选可能不可用。原始语料、媒体及 RAG 索引须由使用者自行配置，不能把已发布索引等同于源码包的一部分。

## 地区筛选资源（Windows Server）

地区资源与政策语料一样，作为**运行时外部资源**提供，不放入源码仓库。需要使用已审核且与当前 RAG 发布批次匹配的四个文件：

- `mainland-province-prefecture-county.json`
- `manifest.json`
- `policy-region-map.json`
- `policy-region-review.json`

如果四个文件已经在旧目录，将 `<original-regions-directory>` 替换成实际旧资源目录，再执行：

```powershell
& ".\scripts\install_regions.ps1" -SourceDir "<original-regions-directory>" -DestinationDir "C:\guance\regions"
& ".\start.ps1" -RegionsDir "C:\guance\regions" -HostAddress "127.0.0.1" -Port 8000
```

**不能将文件放在项目的 `app/resources/regions`，却把环境变量指向不存在的 `C:\guance\regions`。** 两者必须指向同一套有效文件。新启动脚本会明确设置 `GUANCE_POLICY_REGIONS_DIR`，并在缺文件时终止启动；后端会进一步检查地区树哈希、政策映射的版本与 RAG 发布身份是否一致。

使用已有服务器的其他启动服务（如 Windows 服务、NSSM）时，将同样的环境变量设置到对应进程环境里，不能只在别的 PowerShell 窗口设置。

服务启动后，访问 `/api/policies/regions` 和 `/api/policies/facets` 查看目录接口是否可用。上述资源不包含在提交源码和 RAG 数据包中，需从有权访问的原部署环境获取。
