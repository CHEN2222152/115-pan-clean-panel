# 115 网盘定时清理面板

> 编号: project-013
> 创建日期: 2026-07-01
> 状态: 开发中

## 目标

自动清理 115 网盘的"最近接收"文件和"回收站"，带 Web 管理面板和定时任务。

## 功能

- 🔑 115 Cookie 配置与管理
- 📥 手动清理最近接收文件
- 🗑️ 手动清空回收站
- ⏰ Cron 定时任务（默认每天凌晨3点）
- 📋 执行日志查看
- 📁 集成 AList 文件浏览器

## 技术栈

- 后端: Python Flask + APScheduler + requests
- 前端: 原生 HTML + CSS + JS
- 部署: Docker + docker-compose

## 目录结构

`
src/
├── backend/          # Python Flask 后端
│   ├── app.py        # 主入口 + API 路由
│   ├── cleaner.py    # 115 API 客户端
│   ├── scheduler.py  # APScheduler 定时调度
│   ├── config.py     # 配置持久化
│   └── requirements.txt
├── frontend/         # Web 面板前端
│   ├── index.html    # 面板页面
│   ├── style.css     # 样式
│   └── app.js        # 前端逻辑
└── docker/           # 部署配置
    ├── Dockerfile
    └── docker-compose.yml
docs/
├── 架构设计.md
└── 部署说明.md
notes/
└── 踩坑记录.md
`

## 使用

1. 部署到极空间 NAS → 见 docs/部署说明.md
2. 访问 http://NAS_IP:9532
3. 配置 115 Cookie → 设置定时任务
