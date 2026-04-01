"""每日任务生成模块"""
import random
from config import CURRICULUM_FILE, load_json
from content_engine import get_enriched_day_tasks
from tracker import (
    get_progress, get_phase_info, start_if_needed, get_current_day,
    is_open_mode, get_days_until_job, TOTAL_DAYS
)

MOTIVATIONAL_QUOTES = [
    "先跑通mini版本建立直觉，再去读生产级源码。",
    "看不懂源码很正常，先跑起来再说。",
    "每天进步一点点，你会感谢现在的自己。",
    "用乐高拼出一架飞机，远比坐在头等舱里飞行更让人兴奋。",
    "理解>记忆。能用自己的话说出来，才算真懂。",
    "debug一个kernel学到的比看十篇博客多。",
    "nano-vllm 1200行代码读懂了，vLLM十万行也不怕。",
    "今天看不懂的代码，一周后再看可能就豁然开朗。",
    "坚持打卡本身就是一种能力的证明。",
    "你的竞争力 = 你愿意深入的程度。",
    "国产GPU适配需要的就是你这样愿意啃骨头的人。",
    "RL训练不稳定是常态，别被loss吓到。",
    "先读懂数据流，再读懂计算逻辑。",
    "Profile before optimize. 别猜瓶颈在哪。",
    "每个大佬都是从Hello World开始的。",
    "PagedAttention本质就是OS虚拟内存，你已经会了。",
    "MiniMind 64M参数虽小，五脏俱全。",
    "Triton Puzzles刷完，写生产kernel不是梦。",
    "KuiperLLama写进简历，面试官会眼前一亮。",
    "别怕看英文文档，技术英语其实词汇量很小。",
    "保持学习的习惯，比学什么更重要。",
    "GitHub Trending 是最好的技术嗅觉训练场。",
]


def get_today_tasks():
    """获取今日任务"""
    progress = get_progress()
    progress = start_if_needed(progress)

    current_day = get_current_day(progress)

    # 开放学习模式（课程已完成）
    if is_open_mode(current_day):
        return _format_open_mode(current_day, progress)

    curriculum = load_json(CURRICULUM_FILE)
    if not curriculum:
        return None, "❌ 课程数据未找到，请检查 data/curriculum.json"

    phase_info = get_phase_info(current_day)

    # 在所有phase的tasks中找到对应天数的任务
    day_tasks = None
    for phase in curriculum["phases"]:
        for task_day in phase["tasks"]:
            if task_day["day"] == current_day:
                day_tasks = task_day
                break
        if day_tasks:
            break

    if not day_tasks:
        return None, f"🎉 恭喜！你已经完成了全部{TOTAL_DAYS}天的学习计划！\n💡 运行 study feed 查看今日推荐内容继续学习"

    # 从 guides/ 加载丰富内容(key_points, resources)
    day_tasks = get_enriched_day_tasks(day_tasks)

    return _format_today(current_day, phase_info, day_tasks, progress)


def _format_today(day, phase_info, tasks, progress):
    """格式化今日任务输出"""
    quote = random.choice(MOTIVATIONAL_QUOTES)
    streak = progress.get("streak", 0)
    total = progress.get("total_completed", 0)

    # 检查各任务完成状态
    def task_status(task_id):
        if task_id in progress["completed_tasks"]:
            return "✅"
        elif task_id in progress["skipped_tasks"]:
            return "⏭️"
        return "⬜"

    type_icons = {
        "read": "📖",
        "practice": "💻",
        "summary": "📝",
        "leetcode": "🧩"
    }

    lines = [
        "╔══════════════════════════════════════════════════╗",
        f"║  📅 Day {day:>2} / {TOTAL_DAYS}  |  🔥 连续学习: {streak}天  |  ✅ 已完成: {total}",
        f"║  📍 阶段{phase_info['phase_id']}: {phase_info['phase_name']} ({phase_info['day_in_phase']}/{phase_info['total_in_phase']}天)",
        "╠══════════════════════════════════════════════════╣",
        "║",
        "║  🔧 AI Infra任务 (~3h):",
    ]

    for task in tasks.get("infra", []):
        icon = type_icons.get(task["type"], "📌")
        status = task_status(task["id"])
        lines.append(f"║  {status} [{task['id']}] {icon} {task['title']}")
        if task.get("desc"):
            lines.append(f"║      {task['desc']}")
        lines.append(f"║      ⏱️ 预计 {task['duration_min']} 分钟")
        # 显示学习要点
        if task.get("key_points"):
            lines.append("║      📌 学习要点:")
            for kp in task["key_points"]:
                lines.append(f"║        • {kp}")
        # 显示参考资料
        if task.get("resources"):
            lines.append("║      📚 参考资料:")
            for res in task["resources"]:
                lines.append(f"║        → {res['name']}")
                lines.append(f"║          {res['url']}")
        lines.append("║")

    if tasks.get("algo"):
        lines.append("║  📊 算法任务 (~30-60min):")
        for task in tasks.get("algo", []):
            icon = type_icons.get(task["type"], "📌")
            status = task_status(task["id"])
            lines.append(f"║  {status} [{task['id']}] {icon} {task['title']}")
            if task.get("url"):
                lines.append(f"║      🔗 {task['url']}")
            lines.append("║")
    else:
        lines.append("║  📊 算法任务: 今日无，专注Infra!")
        lines.append("║")

    lines.extend([
        "╠══════════════════════════════════════════════════╣",
        f"║  💡 {quote}",
        "╚══════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines), None


def _format_open_mode(current_day, progress):
    """格式化开放学习模式的输出"""
    quote = random.choice(MOTIVATIONAL_QUOTES)
    streak = progress.get("streak", 0)
    total = progress.get("total_completed", 0)
    days_until = get_days_until_job()

    lines = [
        "╔══════════════════════════════════════════════════╗",
        f"║  📅 Day {current_day}  |  🔥 连续学习: {streak}天  |  ✅ 已完成: {total}",
        f"║  🎯 模式: 开放学习（课程已完成 ✨）",
    ]

    if days_until is not None and days_until > 0:
        lines.append(f"║  ⏰ 距离上班还有 {days_until} 天，继续冲！")

    lines.extend([
        "╠══════════════════════════════════════════════════╣",
        "║",
        "║  📡 今日推荐学习内容:",
        "║  运行 study feed 查看 GitHub/知乎/B站 AI热门内容",
        "║",
        "║  💡 建议今日学习方向:",
        "║  1. 浏览 GitHub Trending 找到感兴趣的 AI 项目",
        "║  2. 阅读一篇 AI 相关论文或技术博客",
        "║  3. 动手写代码，实践 > 理论",
        "║",
        "║  📝 记录你的学习:",
        "║  study note <主题> <标题>  — 快速记笔记到 GitHub",
        "║  study sync              — 推送今日学习总结",
        "║",
        "╠══════════════════════════════════════════════════╣",
        f"║  💡 {quote}",
        "╚══════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines), None


def get_today_summary_for_push():
    """生成适合微信/飞书推送的今日任务摘要"""
    progress = get_progress()
    progress = start_if_needed(progress)

    current_day = get_current_day(progress)
    streak = progress.get("streak", 0)
    quote = random.choice(MOTIVATIONAL_QUOTES)

    # 开放学习模式
    if is_open_mode(current_day):
        days_until = get_days_until_job()
        lines = [
            f"📅 Day {current_day} | 🔥 连续{streak}天",
            f"🎯 开放学习模式",
        ]
        if days_until is not None and days_until > 0:
            lines.append(f"⏰ 距离上班还有 {days_until} 天")
        lines.extend([
            "",
            "📡 今日推荐: 运行 study feed 查看",
            "📝 记得用 study sync 同步学习记录",
            "",
            f"💡 {quote}",
        ])
        return "\n".join(lines)

    curriculum = load_json(CURRICULUM_FILE)
    if not curriculum:
        return "课程数据未找到"

    phase_info = get_phase_info(current_day)

    day_tasks = None
    for phase in curriculum["phases"]:
        for task_day in phase["tasks"]:
            if task_day["day"] == current_day:
                day_tasks = task_day
                break
        if day_tasks:
            break

    if not day_tasks:
        return f"🎉 恭喜完成全部{TOTAL_DAYS}天学习计划！"

    # 从 guides/ 加载丰富内容
    day_tasks = get_enriched_day_tasks(day_tasks)

    streak = progress.get("streak", 0)
    days_until = get_days_until_job()
    quote = random.choice(MOTIVATIONAL_QUOTES)

    lines = [
        f"📅 Day {current_day}/{TOTAL_DAYS} | 🔥 连续{streak}天",
        f"📍 阶段{phase_info['phase_id']}: {phase_info['phase_name']} ({phase_info['day_in_phase']}/{phase_info['total_in_phase']}天)",
    ]
    if days_until is not None and days_until > 0:
        lines.append(f"⏰ 距离上班还有 {days_until} 天")
    lines.extend(["", "━━━ 🔧 AI Infra任务 ━━━"])

    for task in day_tasks.get("infra", []):
        status = "✅" if task["id"] in progress["completed_tasks"] else "⬜"
        lines.append(f"\n{status} [{task['id']}] {task['title']}")
        if task.get("desc"):
            lines.append(f"   {task['desc']}")
        # 学习要点
        if task.get("key_points"):
            for kp in task["key_points"][:3]:  # 推送最多3条
                lines.append(f"   • {kp}")
        # 参考资料(推送只放第一个链接)
        if task.get("resources"):
            res = task["resources"][0]
            lines.append(f"   📎 {res['name']}: {res['url']}")

    if day_tasks.get("algo"):
        lines.extend(["", "━━━ 📊 算法任务 ━━━"])
        for task in day_tasks.get("algo", []):
            status = "✅" if task["id"] in progress["completed_tasks"] else "⬜"
            lines.append(f"{status} {task['title']}")
            if task.get("url"):
                lines.append(f"   🔗 {task['url']}")

    lines.extend(["", f"💡 {quote}"])

    return "\n".join(lines)
