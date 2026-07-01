"""定时任务调度器 — 基于 APScheduler"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_job_id = "clean_115_task"


def start():
    """启动调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("调度器已启动")


def stop():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("调度器已停止")


def schedule_task(cron_expr: str, clean_func):
    """设置定时任务"""
    # 移除旧任务
    if scheduler.get_job(_job_id):
        scheduler.remove_job(_job_id)

    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"无效的 cron 表达式: {cron_expr}，需要 5 段")

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )
    scheduler.add_job(clean_func, trigger, id=_job_id, replace_existing=True)
    logger.info(f"定时任务已设置: {cron_expr}")


def remove_task():
    """移除定时任务"""
    if scheduler.get_job(_job_id):
        scheduler.remove_job(_job_id)
        logger.info("定时任务已移除")


def get_next_run() -> str:
    """获取下次执行时间"""
    job = scheduler.get_job(_job_id)
    if job and job.next_run_time:
        return job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
    return "未设置"
