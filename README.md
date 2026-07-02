# 🗑️ 115 网盘定时清理面板

自动清理 115 网盘的 **最近接收** 文件和 **回收站**，带 Web 管理面板和 Cron 定时任务。

> 🌐 **面板地址**: `http://<你的IP>:9532`
> 📁 **集成 AList 文件浏览器**: `http://<你的IP>:9533`

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🔑 **Cookie 管理** | 从浏览器粘贴 115 Cookie，保存在 Docker 卷中不会丢失 |
| 📥 **清理最近接收** | 自动搜索并删除 115 最近接收的文件 |
| 🗑️ **清空回收站** | 一键清空 115 网盘回收站 |
| ⏰ **定时任务** | Cron 表达式配置自动清理（默认每天凌晨 0 点） |
| 📋 **执行日志** | 查看每次清理的历史记录 |
| 📁 **AList 集成** | 附带 AList 文件浏览器，可直接浏览管理 115 文件 |

## 🚀 快速部署

### docker-compose（推荐）

```bash
git clone https://github.com/CHEN2222152/115-pan-clean-panel.git
cd 115-pan-clean-panel
docker compose up -d
```

> 如果服务器无法访问 Docker Hub，先拉取基础镜像：
> ```bash
> docker pull registry.zenithspace.net/library/python:3.12-slim
> docker tag registry.zenithspace.net/library/python:3.12-slim python:3.12-slim
> docker compose build
> docker compose up -d
> ```

## 🎯 使用步骤

### 1. 打开面板
访问 `http://<你的IP>:9532`

### 2. 配置 115 Cookie
1. 在浏览器登录 [115.com](https://115.com)
2. F12 → 网络 → 刷新页面 → 复制任意请求的 Cookie
3. 粘贴到面板 → **保存 Cookie** → **验证 Cookie**

### 3. 设置定时任务
- Cron 默认 `0 0 * * *`（每天凌晨 0 点）
- 点 **启用定时** 即可

### 4. AList 文件浏览器
访问 `http://<你的IP>:9533`
- 默认账号: `admin`
- 首次密码: `docker logs alist | grep password`
- 后台 → 存储 → 添加 115 Cloud 驱动

## 🔧 Cron 表达式参考

| 表达式 | 说明 |
|--------|------|
| `0 0 * * *` | 每天凌晨 0 点 |
| `0 */6 * * *` | 每 6 小时 |
| `0 3 * * *` | 每天凌晨 3 点 |

## ⚠️ 注意事项

- Cookie 会过期（通常几周到几个月），过期后需重新粘贴
- 清理操作不可撤销，文件会被永久删除
- 面板无登录认证，请勿暴露到公网

## 🛠️ 技术栈

- **后端**: Python Flask + APScheduler + requests
- **前端**: 原生 HTML + CSS + Vanilla JS
- **部署**: Docker + docker-compose
- **文件浏览器**: [AList](https://github.com/AlistGo/alist)



## 👹 当前已知状态

> **📻 最近接收** — ✅ 正常运行，定时任务每天凌晨自动清理
>
> **🗑️ 回收站** — ⏳ 115 服务端的 /rb/* 回收站接口（/rb/list、/rb/empty 等）当前全部返回“服务器开小差了，稍后再试吧”。这是 115 服务端问题，非代码 bug。
>
> 代码已做了容错处理：检测到服务不可用时跳过无用重试，避免反复请求消耗时间；
> 等 115 修复后，回收站清空功能会自动恢复，无需改代码。
>
> 如果你遇到同样问题，说明 115 服务端暂未修复，耐心等待即可。

## 📁 项目结构

```
src/
├── backend/           # Python Flask 后端
│   ├── app.py         # 主入口 + REST API
│   ├── cleaner.py     # 115 API 客户端
│   ├── scheduler.py   # APScheduler 定时调度
│   ├── config.py      # 配置持久化
│   └── requirements.txt
├── frontend/          # Web 面板前端
│   ├── index.html     # 面板页面
│   ├── style.css      # 样式
│   └── app.js         # 前端交互
└── docker/            # 部署配置
    ├── Dockerfile
    └── docker-compose.yml
```