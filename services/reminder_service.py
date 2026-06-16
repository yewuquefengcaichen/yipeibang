"""
定时提醒服务
使用APScheduler实现定时任务
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio


# 全局调度器
scheduler = None


def init_scheduler():
    """初始化调度器"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()
        print("Reminder scheduler started")
    return scheduler


def add_reminder(
    reminder_id: str,
    title: str,
    trigger_time: datetime,
    callback_func,
    **kwargs
):
    """添加单次提醒"""
    if scheduler is None:
        init_scheduler()

    scheduler.add_job(
        callback_func,
        'date',
        run_date=trigger_time,
        id=reminder_id,
        kwargs=kwargs,
        replace_existing=True
    )
    print(f"Added reminder: {reminder_id} at {trigger_time}")


def add_recurring_reminder(
    reminder_id: str,
    title: str,
    cron_expr: str,
    callback_func,
    **kwargs
):
    """添加周期性提醒（使用cron表达式）"""
    if scheduler is None:
        init_scheduler()

    # 解析cron表达式
    parts = cron_expr.split()
    if len(parts) == 5:
        minute, hour, day, month, day_of_week = parts

        scheduler.add_job(
            callback_func,
            CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            ),
            id=reminder_id,
            kwargs=kwargs,
            replace_existing=True
        )
        print(f"Added recurring reminder: {reminder_id} with cron: {cron_expr}")


def remove_reminder(reminder_id: str):
    """移除提醒"""
    if scheduler and scheduler.get_job(reminder_id):
        scheduler.remove_job(reminder_id)
        print(f"Removed reminder: {reminder_id}")


def get_all_reminders() -> List[Dict]:
    """获取所有活跃的提醒任务"""
    if scheduler is None:
        return []

    jobs = scheduler.get_jobs()
    reminders = []

    for job in jobs:
        reminders.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })

    return reminders


# 提醒回调函数
async def reminder_callback(reminder_id: str, title: str, content: str, user_id: str = "default_user"):
    """提醒触发时的回调函数"""
    print(f"[REMINDER] {title}: {content}")

    # 更新数据库状态
    from utils.database import update_reminder_status
    update_reminder_status(reminder_id, "completed")

    # TODO: 实现浏览器通知
    # 可以通过WebSocket或SSE推送到前端


def schedule_appointment_reminder(
    appointment_id: str,
    appointment_time: datetime,
    title: str,
    content: str,
    advance_hours: int = 24
):
    """安排就诊提醒（提前N小时提醒）"""
    reminder_time = appointment_time - timedelta(hours=advance_hours)

    if reminder_time > datetime.now():
        add_reminder(
            reminder_id=f"appt_{appointment_id}",
            title=title,
            trigger_time=reminder_time,
            callback_func=reminder_callback,
            reminder_id=appointment_id,
            title=title,
            content=content
        )


def schedule_medication_reminder(
    medication_id: str,
    title: str,
    times_per_day: List[str],  # ["08:00", "12:00", "18:00"]
    user_id: str = "default_user"
):
    """安排用药提醒（每天固定时间）"""
    for time_str in times_per_day:
        hour, minute = time_str.split(':')
        reminder_id = f"med_{medication_id}_{hour}{minute}"

        add_recurring_reminder(
            reminder_id=reminder_id,
            title=title,
            cron_expr=f"{minute} {hour} * * *",  # 每天固定时间
            callback_func=reminder_callback,
            reminder_id=reminder_id,
            title=title,
            content=f"该服用{title}了"
        )


def load_reminders_from_database():
    """从数据库加载提醒任务"""
    from utils.database import get_active_reminders

    reminders = get_active_reminders()

    for reminder in reminders:
        trigger_time = datetime.fromisoformat(reminder['trigger_time'])

        if trigger_time > datetime.now():
            add_reminder(
                reminder_id=reminder['id'],
                title=reminder['title'],
                trigger_time=trigger_time,
                callback_func=reminder_callback,
                reminder_id=reminder['id'],
                title=reminder['title'],
                content=reminder['content']
            )


if __name__ == "__main__":
    # 测试代码
    print("=== Reminder Service Test ===\n")

    init_scheduler()

    # 测试单次提醒（5秒后）
    test_time = datetime.now() + timedelta(seconds=5)
    add_reminder(
        reminder_id="test_001",
        title="测试提醒",
        trigger_time=test_time,
        callback_func=reminder_callback,
        reminder_id="test_001",
        title="测试提醒",
        content="这是一个测试提醒"
    )

    # 测试周期性提醒（每分钟）
    add_recurring_reminder(
        reminder_id="test_recurring",
        title="每分钟提醒",
        cron_expr="* * * * *",
        callback_func=reminder_callback,
        reminder_id="test_recurring",
        title="每分钟提醒",
        content="这是一个周期性提醒"
    )

    print("\n活跃的提醒任务：")
    for reminder in get_all_reminders():
        print(f"- {reminder['id']}: {reminder['next_run_time']}")

    # 保持运行
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nScheduler stopped")
