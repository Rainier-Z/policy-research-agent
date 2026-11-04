# Web Frontend（React + Vite）

位于 `web/frontend/src/`，包含研究会话、结果展示、政策目录和研究专题页面。运行时从 Web 后端读取政策数据，不在源码中附带政策语料数据集。

要求 Node.js 22+。在 `web/frontend` 目录执行：

```powershell
npm ci
npm run dev
```

默认 API 为 `http://127.0.0.1:8000`，可以在本机通过 `.env` 设置 `VITE_API_BASE_URL`；`VITE_RESEARCH_MODE=real` 使用真实后端。不要把凭据写入前端环境文件。

编译：`npm run build`。
