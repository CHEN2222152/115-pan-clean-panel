"""配置管理 — 持久化存储 115 Cookie 和定时任务设置"""
import json
import os

CONFIG_FILE = os.environ.get("CONFIG_FILE", "/data/config.json")


def load_config() -> dict:
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cookies": {}, "schedule": {"enabled": False, "cron": "0 3 * * *", "tasks": []}}


def save_config(config: dict):
    """保存配置"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_cookies() -> dict:
    """获取 115 Cookie"""
    cfg = load_config()
    return cfg.get("cookies", {})


def save_cookies(cookies: dict):
    """保存 115 Cookie"""
    cfg = load_config()
    cfg["cookies"] = cookies
    save_config(cfg)


def get_schedule() -> dict:
    """获取定时任务配置"""
    cfg = load_config()
    return cfg.get("schedule", {"enabled": False, "cron": "0 3 * * *", "tasks": []})


def save_schedule(schedule: dict):
    """保存定时任务配置"""
    cfg = load_config()
    cfg["schedule"] = schedule
    save_config(cfg)
