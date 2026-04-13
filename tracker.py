"""进度追踪模块"""
import json
from datetime import datetime, timedelta
from config import PROGRESS_FILE, load_json, save_json, get_config

# 总天数
TOTAL_DAYS = 18


def get_progress():
    """获取当前进度"""
    progress = load_json(PROGRESS_FILE)
    if not progress:
        progress = {
            "start_date": None,
            "current_day": 0,
            "completed_tasks": [],
            "skipped_tasks": [],
            "daily_logs": {},
            "quiz_history": [],
            "streak": 0,
            "max_streak": 0,
            "total_completed": 0
        }
    return progress


def save_progress(progress):
    """保存进度"""
    save_json(PROGRESS_FILE, progress)


def start_if_needed(progress):
    """如果尚未开始，初始化开始日期"""
    if not progress["start_date"]:
        progress["start_date"] = datetime.now().strftime("%Y-%m-%d")
        progress["current_day"] = 1
        save_progress(progress)
    return progress


def get_current_day(progress):
    """根据日期计算当前天数（不设上限，支持持续学习）"""
    if not progress["start_date"]:
        return 0

    start = datetime.strptime(progress["start_date"], "%Y-%m-%d")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    delta = (today - start).days + 1

    return max(delta, 1)


def is_open_mode(current_day):
    """判断是否进入开放学习模式（课程结束后）"""
    return current_day > TOTAL_DAYS


def get_days_until_job():
    """获取距离上班的天数"""
    config = get_config()
    job_date_str = config.get("job_start_date", "")
    if not job_date_str:
        return None
    try:
        job_date = datetime.strptime(job_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (job_date - today).days
        return delta
    except ValueError:
        return None


def mark_done(progress, task_id):
    """标记任务完成"""
    today_str = datetime.now().strftime("%Y-%m-%d")

    if task_id in progress["completed_tasks"]:
        return False, "该任务已经完成过了"

    progress["completed_tasks"].append(task_id)
    progress["total_completed"] += 1

    # 更新每日日志
    if today_str not in progress["daily_logs"]:
        progress["daily_logs"][today_str] = {
            "completed": [],
            "study_started": datetime.now().strftime("%H:%M")
        }
    progress["daily_logs"][today_str]["completed"].append(task_id)

    # 更新连续打卡
    _update_streak(progress)

    save_progress(progress)
    return True, f"✅ 任务 {task_id} 已标记完成！"


def mark_skip(progress, task_id, reason=""):
    """跳过任务"""
    if task_id in progress["skipped_tasks"]:
        return False, "该任务已经跳过了"

    progress["skipped_tasks"].append(task_id)
    today_str = datetime.now().strftime("%Y-%m-%d")

    if today_str not in progress["daily_logs"]:
        progress["daily_logs"][today_str] = {"completed": [], "skipped": []}

    if "skipped" not in progress["daily_logs"][today_str]:
        progress["daily_logs"][today_str]["skipped"] = []
    progress["daily_logs"][today_str]["skipped"].append({
        "task_id": task_id,
        "reason": reason
    })

    save_progress(progress)
    return True, f"⏭️ 任务 {task_id} 已跳过"


def _update_streak(progress):
    """更新连续打卡天数（分层连胜系统）

    分层规则:
    - micro: 答3道quiz或复习5张闪卡（最低门槛，维持streak）
    - plan: 完成当日全部计划任务（bonus）
    - demo: 通过技能验证挑战（bonus）
    """
    today = datetime.now().date()
    streak = 0
    layer_best = "none"

    for i in range(365):
        check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        day_log = progress["daily_logs"].get(check_date, {})

        has_micro = day_log.get("micro_achieved", False)
        has_plan = day_log.get("plan_achieved", False)
        has_demo = day_log.get("demo_achieved", False)

        if has_micro or has_plan or has_demo or day_log.get("completed"):
            streak += 1
            # 记录今天最好的层级
            if i == 0:
                if has_demo:
                    layer_best = "demo"
                elif has_plan:
                    layer_best = "plan"
                elif has_micro:
                    layer_best = "micro"
                else:
                    layer_best = "micro"  # 旧数据兼容
        else:
            if i == 0:
                continue
            break

    progress["streak"] = streak
    progress["streak_layer"] = layer_best
    progress["max_streak"] = max(progress.get("max_streak", 0), streak)


def record_streak_layer(layer):
    """记录今日streak层级达成

    Args:
        layer: "micro" | "plan" | "demo"
    """
    progress = get_progress()
    today_str = datetime.now().strftime("%Y-%m-%d")

    if today_str not in progress["daily_logs"]:
        progress["daily_logs"][today_str] = {
            "completed": [],
            "study_started": datetime.now().strftime("%H:%M"),
        }

    log = progress["daily_logs"][today_str]
    layer_key = f"{layer}_achieved"

    if log.get(layer_key):
        return f"今日{layer}已达成"

    log[layer_key] = True
    _update_streak(progress)
    save_progress(progress)

    labels = {"micro": "最低门槛✅", "plan": "计划完成🏆", "demo": "技能验证🎯"}
    return f"✅ 今日{layer}达成！{labels.get(layer, '')} 连续{progress['streak']}天"


def check_micro_achieved(progress=None):
    """检查今日micro是否达成（答3道quiz或复习5张闪卡）"""
    if progress is None:
        progress = get_progress()

    today_str = datetime.now().strftime("%Y-%m-%d")
    log = progress.get("daily_logs", {}).get(today_str, {})

    # 直接标记
    if log.get("micro_achieved"):
        return True

    # 基于quiz答题数判断
    quiz_count = log.get("quiz_answers_today", 0)
    flashcard_reviews = log.get("flashcard_reviews_today", 0)

    return quiz_count >= 3 or flashcard_reviews >= 5


def get_day_completion_rate(progress, day_tasks):
    """计算某天的任务完成率"""
    if not day_tasks:
        return 0.0

    all_task_ids = []
    for task in day_tasks.get("infra", []):
        all_task_ids.append(task["id"])
    for task in day_tasks.get("algo", []):
        all_task_ids.append(task["id"])

    if not all_task_ids:
        return 0.0

    completed = sum(1 for tid in all_task_ids if tid in progress["completed_tasks"])
    return completed / len(all_task_ids)


def get_phase_info(day):
    """根据天数返回所在阶段信息"""
    phases = [
        (1,  2, 1, "量化基础 (Lec5)"),
        (3,  5, 2, "量化进阶+LLM量化 (Lec6,14)"),
        (6,  7, 3, "剪枝 (Lec3,4)"),
        (8,  9, 4, "NAS (Lec7,8)"),
        (10, 10, 5, "知识蒸馏 (Lec9)"),
        (11, 12, 6, "LLM推理优化 (Lec12,13)"),
        (13, 14, 7, "长上下文+视觉模型 (Lec15,16)"),
        (15, 16, 8, "分布式训练 (Lec19,20)"),
        (17, 17, 9, "边缘部署+高效训练 (Lec10,11,21)"),
        (18, 18, 10, "总结复盘"),
    ]
    for start, end, phase_id, name in phases:
        if start <= day <= end:
            day_in_phase = day - start + 1
            total_in_phase = end - start + 1
            return {
                "phase_id": phase_id,
                "phase_name": name,
                "day_in_phase": day_in_phase,
                "total_in_phase": total_in_phase
            }
    return {"phase_id": 6, "phase_name": "已完成全部课程!", "day_in_phase": 0, "total_in_phase": 0}


def generate_week_report(progress):
    """生成周报"""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    report_lines = []
    total_completed = 0
    active_days = 0

    for i in range(7):
        date = week_start + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        day_name = ["一", "二", "三", "四", "五", "六", "日"][i]

        if date_str in progress["daily_logs"]:
            day_log = progress["daily_logs"][date_str]
            count = len(day_log.get("completed", []))
            total_completed += count
            if count > 0:
                active_days += 1
            status = f"✅ 完成 {count} 个任务"
        elif date <= today:
            status = "❌ 未学习"
        else:
            status = "⬜ 未到"

        report_lines.append(f"  周{day_name} ({date_str}): {status}")

    report = [
        "╔══════════════════════════════════════╗",
        "║           📊 本周学习周报              ║",
        "╠══════════════════════════════════════╣",
    ]
    for line in report_lines:
        report.append(f"║ {line:<36} ║")
    report.extend([
        "╠══════════════════════════════════════╣",
        f"║  📈 本周完成任务: {total_completed:<20}║",
        f"║  📅 学习天数: {active_days}/7{' ':>21}║",
        f"║  🔥 当前连续: {progress['streak']}天{' ':>21}║",
        f"║  🏆 最长连续: {progress.get('max_streak', 0)}天{' ':>21}║",
        "╚══════════════════════════════════════╝",
    ])
    return "\n".join(report)
