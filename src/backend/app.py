import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

from config import load_config, save_config, get_cookies, save_cookies, get_schedule, save_schedule
from cleaner import Pan115Cleaner
from scheduler import start as sched_start, schedule_task, remove_task, get_next_run

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=None)

LOG_FILE = os.environ.get("LOG_FILE", "/data/clean_log.txt")
FRONTEND_DIR = os.environ.get("FRONTEND_DIR", "/app/frontend")


def append_log(message):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    logger.info(line)


def read_logs(n=100):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [l.strip() for l in lines[-n:]]


def get_cleaner():
    cookies = get_cookies()
    if not cookies:
        raise ValueError("115 Cookie 未配置")
    return Pan115Cleaner(cookies)


def run_clean_tasks():
    logs = []
    try:
        cleaner = get_cleaner()
        logs.append("115 Cookie 验证通过")
        r1 = cleaner.clean_received()
        logs.append(f"Received files: {r1['message']}")
        append_log(f"Clean received: {r1['message']} ({r1.get('deleted', 0)} files)")
        r2 = cleaner.clean_recycle_bin()
        logs.append(f"Recycle bin: {r2['message']}")
        append_log(f"Clear recycle bin: {r2['message']}")
    except Exception as e:
        err_msg = f"Clean failed: {str(e)}"
        logs.append(err_msg)
        append_log(err_msg)
        logger.exception("Clean task error")
    return "\n".join(logs)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/api/cookies", methods=["GET"])
def api_get_cookies():
    cookies = get_cookies()
    has_cookies = bool(cookies and cookies.get("UID"))
    return jsonify({"configured": has_cookies})


@app.route("/api/cookies", methods=["POST"])
def api_set_cookies():
    data = request.get_json()
    cookies = data.get("cookies", {})
    if not cookies:
        return jsonify({"success": False, "error": "请提供 Cookie"}), 400
    save_cookies(cookies)
    append_log("115 Cookie 已更新")
    return jsonify({"success": True})


@app.route("/api/verify", methods=["POST"])
def api_verify():
    try:
        cleaner = get_cleaner()
        result = cleaner.verify()
        if result.get("state"):
            user = result.get("data", "")
            if isinstance(user, dict):
                user = user.get("user_name", str(user))
            return jsonify({"success": True, "user": str(user)})
        return jsonify({"success": False, "error": result.get("error", "验证失败")})
    except Exception as e:
        logger.exception("Verify error")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/clean/received", methods=["POST"])
def api_clean_received():
    try:
        cleaner = get_cleaner()
        result = cleaner.clean_received()
        append_log(f"Manual clean received: {result['message']}")
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/clean/recycle", methods=["POST"])
def api_clean_recycle():
    try:
        cleaner = get_cleaner()
        result = cleaner.clean_recycle_bin()
        append_log(f"Manual clean recycle: {result['message']}")
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/clean/all", methods=["POST"])
def api_clean_all():
    result = run_clean_tasks()
    return jsonify({"success": True, "message": result})


@app.route("/api/schedule", methods=["GET"])
def api_get_schedule():
    sched = get_schedule()
    return jsonify({
        "enabled": sched.get("enabled", False),
        "cron": sched.get("cron", "0 3 * * *"),
        "next_run": get_next_run(),
    })


@app.route("/api/schedule", methods=["POST"])
def api_set_schedule():
    data = request.get_json()
    enabled = data.get("enabled", False)
    cron = data.get("cron", "0 3 * * *")
    save_schedule({"enabled": enabled, "cron": cron, "tasks": ["clean_received", "clean_recycle"]})
    if enabled:
        schedule_task(cron, run_clean_tasks)
        append_log(f"Schedule enabled: {cron}")
    else:
        remove_task()
        append_log("定时任务已禁用")
    return jsonify({"success": True, "enabled": enabled, "cron": cron, "next_run": get_next_run()})


@app.route("/api/logs", methods=["GET"])
def api_get_logs():
    n = request.args.get("n", 100, type=int)
    return jsonify({"logs": read_logs(n)})


if __name__ == "__main__":
    sched = get_schedule()
    if sched.get("enabled"):
        try:
            schedule_task(sched["cron"], run_clean_tasks)
            logger.info(f"Schedule restored: {sched['cron']}")
        except Exception as e:
            logger.error(f"Schedule restore failed: {e}")
    sched_start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
