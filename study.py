#!/usr/bin/env python3
"""
AI Study CLI - AI Infra学习助手
================================
一个帮助你系统学习AI基础设施知识的命令行工具。
4天韩松EfficientML速览课程

用法:
  python study.py today          - 查看今日学习任务
  python study.py done <任务ID>  - 标记任务完成
  python study.py status         - 查看总体进度
  python study.py quiz           - 知识自测
  python study.py quiz-done <ID> <understand|fuzzy|not> - 记录答题结果
  python study.py resources      - 查看当前阶段资料
  python study.py add <url> [标签] - 添加自定义资料
  python study.py feed           - 查看今日AI热门推荐(GitHub/知乎/B站)
  python study.py feed refresh   - 强制刷新今日推荐
  python study.py flash          - 刷闪卡（间隔复习）
  python study.py flash-answer <ID> - 查看闪卡答案
  python study.py flash-ok <ID>  - 标记闪卡：记住了
  python study.py flash-fail <ID> - 标记闪卡：没记住
  python study.py flash-stats    - 闪卡统计
  python study.py note <主题> <标题> - 快速记录笔记到GitHub
  python study.py sync           - 推送今日学习总结到GitHub
  python study.py refresh        - 从guides重新生成闪卡库
  python study.py history        - 查看历史记录
  python study.py week           - 本周学习周报
  python study.py init           - 首次初始化(微信/飞书/GitHub配置)
  python study.py notify         - 发送推送通知(微信+飞书)
  python study.py notify test    - 测试推送
  python study.py remind [HH:MM] - 设置定时提醒
"""

import sys
import os

# 确保项目目录在path中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows 终端编码修复
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import get_config, init_config, save_config
from tracker import (
    get_progress, save_progress, mark_done, mark_skip,
    get_current_day, get_phase_info, generate_week_report, start_if_needed,
    is_open_mode, get_days_until_job, TOTAL_DAYS
)
from planner import get_today_tasks, get_today_summary_for_push
from quiz import get_quiz_questions, record_quiz_result, format_quiz, get_quiz_stats
from resources import get_phase_resources, add_custom_resource
from notifier import (
    push_wechat, push_feishu, push_telegram, send_daily_reminder,
    send_evening_reminder, setup_windows_schedule
)


def cmd_today():
    """显示今日任务"""
    output, error = get_today_tasks()
    if error:
        print(error)
    else:
        print(output)


def cmd_done(task_id):
    """标记任务完成"""
    progress = get_progress()
    success, msg = mark_done(progress, task_id)
    print(msg)

    # 检查今日是否全部完成（仅课程模式）
    if success:
        current_day = get_current_day(progress)
        if not is_open_mode(current_day):
            from config import CURRICULUM_FILE, load_json
            curriculum = load_json(CURRICULUM_FILE)
            day_tasks = None
            for phase in curriculum["phases"]:
                for task_day in phase["tasks"]:
                    if task_day["day"] == current_day:
                        day_tasks = task_day
                        break
                if day_tasks:
                    break

            if day_tasks:
                all_ids = [t["id"] for t in day_tasks.get("infra", [])] + \
                          [t["id"] for t in day_tasks.get("algo", [])]
                completed = [tid for tid in all_ids if tid in progress["completed_tasks"]]
                remaining = len(all_ids) - len(completed)
                if remaining == 0:
                    print("\n🎉 今日任务全部完成！太棒了！明天继续加油！")
                    print("💡 运行 study sync 推送今日学习总结到 GitHub")
                else:
                    print(f"\n📌 今日还剩 {remaining} 个任务未完成")
        else:
            print("💡 运行 study sync 推送今日学习总结到 GitHub")


def cmd_skip(task_id, reason=""):
    """跳过任务"""
    progress = get_progress()
    success, msg = mark_skip(progress, task_id, reason)
    print(msg)


def cmd_status():
    """显示总体进度"""
    progress = get_progress()

    if not progress.get("start_date"):
        print("📝 还未开始学习，运行 'python study.py today' 开始吧！")
        return

    current_day = get_current_day(progress)
    phase_info = get_phase_info(current_day)
    total_completed = progress.get("total_completed", 0)
    streak = progress.get("streak", 0)
    max_streak = progress.get("max_streak", 0)
    days_until = get_days_until_job()

    # 进度条：课程内显示课程进度，课程外显示持续学习天数
    if not is_open_mode(current_day):
        progress_bar_len = 30
        progress_pct = current_day / TOTAL_DAYS
        filled = int(progress_bar_len * progress_pct)
        bar = "█" * filled + "░" * (progress_bar_len - filled)
        day_display = f"Day {current_day} / {TOTAL_DAYS}"
        bar_display = f"[{bar}] {progress_pct*100:.0f}%"
        mode_display = f"📍 当前阶段: {phase_info['phase_name']}\n║     阶段进度: {phase_info['day_in_phase']} / {phase_info['total_in_phase']} 天"
    else:
        extra_days = current_day - TOTAL_DAYS
        day_display = f"Day {current_day} (课程完成 + 持续学习第 {extra_days} 天)"
        bar_display = f"[{'█' * 30}] 课程 100% ✨"
        mode_display = "🎯 模式: 开放学习（每日 GitHub/知乎/B站 推荐）"

    countdown = ""
    if days_until is not None:
        if days_until > 0:
            countdown = f"\n║  ⏰ 距离上班还有 {days_until} 天"
        elif days_until == 0:
            countdown = "\n║  🎉 今天就是上班第一天！加油！"
        else:
            countdown = f"\n║  💼 已上班 {-days_until} 天，保持学习节奏！"

    print(f"""
╔══════════════════════════════════════════════════╗
║              📊 学习进度总览                       ║
╠══════════════════════════════════════════════════╣
║
║  📅 开始日期: {progress['start_date']}
║  📍 当前: {day_display}
║  {bar_display}
║
║  {mode_display}{countdown}
║
║  ✅ 已完成任务: {total_completed} 个
║  🔥 连续学习: {streak} 天
║  🏆 最长连续: {max_streak} 天
║
║  {get_quiz_stats(progress)}
║
╚══════════════════════════════════════════════════╝
""")


def cmd_feed(refresh=False):
    """查看今日AI热门推荐"""
    from fetcher import fetch_daily_recommendations, format_recommendations

    print("📡 正在获取今日AI学习推荐...\n")
    data = fetch_daily_recommendations(force_refresh=refresh)
    print(format_recommendations(data))


def cmd_flash(count=5):
    """刷闪卡"""
    from flashcard import get_due_cards, format_card_front, format_flashcard_stats

    cards = get_due_cards(count)
    if not cards:
        print("🎉 今日没有待复习的闪卡！")
        print("\n" + format_flashcard_stats())
        return

    print(f"🃏 今日待复习: {len(cards)} 张闪卡\n")
    for card in cards:
        print(format_card_front(card))
        print()


def cmd_flash_answer(card_id):
    """查看闪卡答案"""
    from flashcard import find_card, format_card_back

    card = find_card(card_id)
    if not card:
        print(f"❌ 找不到闪卡: {card_id}")
        return
    print(format_card_back(card))


def cmd_flash_review(card_id, remembered):
    """记录闪卡复习结果"""
    from flashcard import find_card, review_card

    card = find_card(card_id)
    if not card:
        print(f"❌ 找不到闪卡: {card_id}")
        return
    result = review_card(card_id, remembered)
    print(result)


def cmd_flash_stats():
    """闪卡统计"""
    from flashcard import format_flashcard_stats
    print(format_flashcard_stats())


def cmd_note(topic, title_text):
    """快速记录笔记到GitHub"""
    from github_sync import resolve_topic_dir, sync_note
    from datetime import datetime

    topic_dir = resolve_topic_dir(topic)
    today = datetime.now().strftime("%Y-%m-%d")
    # 生成文件名
    safe_title = title_text.replace(" ", "_").replace("/", "-")[:50]
    filename = f"{today}_{safe_title}.md"

    # 生成笔记内容
    content = f"# {title_text}\n\n> {today} | 主题: {topic}\n\n## 笔记\n\n(待补充)\n\n---\n*Generated by AI Study CLI*\n"

    print(f"📝 正在推送笔记到 {topic_dir}/{filename}...")
    ok, msg = sync_note(topic_dir, filename, content)
    print(f"{'✅' if ok else '❌'} {msg}")


def cmd_sync():
    """推送今日学习总结到GitHub"""
    from github_sync import sync_daily_summary

    progress = get_progress()
    current_day = get_current_day(progress)
    phase_info = get_phase_info(current_day)

    print("📤 正在推送今日学习总结到 GitHub...")
    ok, msg = sync_daily_summary(progress, current_day, phase_info)
    print(f"{'✅' if ok else '❌'} {msg}")


def cmd_refresh():
    """从guides重新生成闪卡库"""
    from content_engine import generate_flashcards_from_guides

    print("🔄 正在从 guides/ 重新生成闪卡库...")
    count = generate_flashcards_from_guides()
    print(f"✅ 已生成 {count} 张闪卡到 data/flashcards.json")


def cmd_project():
    """显示当前阶段的实战项目"""
    from content_engine import load_project_for_phase

    progress = get_progress()
    progress = start_if_needed(progress)
    current_day = get_current_day(progress)
    phase_info = get_phase_info(current_day)

    project = load_project_for_phase(phase_info["phase_id"])
    if not project:
        print("当前阶段没有关联的实战项目")
        return

    lines = [
        "╔══════════════════════════════════════════════════╗",
        f"║  🎯 阶段{phase_info['phase_id']} 实战项目",
        "╠══════════════════════════════════════════════════╣",
        "║",
        f"║  📦 {project['title']}",
        f"║  {project['description']}",
        "║",
        f"║  🏆 交付目标:",
        f"║  {project['deliverable']}",
        "║",
        "║  📋 里程碑:",
    ]

    for m in project.get("milestones", []):
        if m["day"] < current_day:
            status = "✅"
        elif m["day"] == current_day:
            status = "🔄"
        else:
            status = "⬜"
        lines.append(f"║  {status} Day {m['day']}: {m['task']}")
        lines.append(f"║       {m['desc']}")

    lines.extend([
        "║",
        "╚══════════════════════════════════════════════════╝",
    ])
    print("\n".join(lines))


def cmd_tutor():
    """显示交互式辅导使用说明"""
    progress = get_progress()
    progress = start_if_needed(progress)
    current_day = get_current_day(progress)
    phase_info = get_phase_info(current_day)

    print(f"""
╔══════════════════════════════════════════════════╗
║          🎓 Interactive Tutor Mode                ║
╠══════════════════════════════════════════════════╣
║
║  当前: Day {current_day} ({phase_info['phase_name']})
║
║  在 Claude Code 中使用以下命令开始交互学习:
║
║  /study-tutor          - 今日任务逐步引导学习
║  /study-dive <主题>    - 深度专题学习
║  /study-code           - 编程练习(按阶段出题)
║  /study-review         - 交互式闪卡复习
║
║  也可以直接用自然语言:
║  "帮我理解今天的任务"
║  "解释一下 MACA 和 CUDA 的区别"
║  "出个 Triton 编程练习题"
║
╚══════════════════════════════════════════════════╝
""")


def cmd_generate(subcmd=""):
    """动态内容生成"""
    if subcmd == "quiz":
        from generate_content import generate_missing_quizzes
        count = generate_missing_quizzes()
        print(f"✅ 已生成 {count} 道新quiz题")
    elif subcmd == "flash":
        from generate_content import generate_missing_flashcards
        count = generate_missing_flashcards()
        print(f"✅ 闪卡库已刷新，共 {count} 张闪卡")
    elif subcmd == "resources":
        from generate_content import generate_resources_from_keywords
        keywords = input("请输入关键词(空格分隔): ").strip().split()
        resources = generate_resources_from_keywords(keywords)
        for res in resources:
            print(f"  → {res['name']}: {res['url']}")
    else:
        print("用法: study generate <quiz|flash|resources>")
        print("  quiz      - 为没有quiz的任务自动生成题目")
        print("  flash     - 刷新闪卡库")
        print("  resources - 从关键词生成资源搜索链接")


def cmd_quiz():
    """知识自测"""
    questions, error = get_quiz_questions(3)
    if error:
        print(error)
    else:
        print(format_quiz(questions))


def cmd_quiz_done(quiz_id, confidence):
    """记录答题结果"""
    # 支持简写
    if confidence == "not":
        confidence = "not_understand"

    if confidence not in ("understand", "fuzzy", "not_understand"):
        print(f"❌ 无效的自评结果，请使用: understand / fuzzy / not")
        return

    record_quiz_result(quiz_id, confidence)
    labels = {"understand": "✅ 理解", "fuzzy": "🟡 模糊", "not_understand": "❌ 不会"}
    print(f"已记录: {quiz_id} → {labels[confidence]}")

    if confidence == "not_understand":
        print("💡 这道题会在明天再次出现，帮你巩固！")
    elif confidence == "fuzzy":
        print("💡 这道题会在3天后再次出现复习。")
    else:
        print("💡 这道题会在7天后再次出现，保持记忆！")


def cmd_resources():
    """查看当前阶段资料"""
    print(get_phase_resources())


def cmd_add_resource(url, tag=""):
    """添加自定义资料"""
    result = add_custom_resource(url, tag)
    print(result)


def cmd_history():
    """查看历史记录"""
    progress = get_progress()
    logs = progress.get("daily_logs", {})

    if not logs:
        print("📝 还没有学习记录")
        return

    # 显示最近7天的记录
    sorted_dates = sorted(logs.keys(), reverse=True)[:7]

    print("╔══════════════════════════════════════╗")
    print("║         📜 最近学习记录               ║")
    print("╠══════════════════════════════════════╣")

    for date_str in sorted_dates:
        log = logs[date_str]
        completed_count = len(log.get("completed", []))
        skipped_count = len(log.get("skipped", []))
        start_time = log.get("study_started", "??:??")
        print(f"║ {date_str} | ✅{completed_count} ⏭️{skipped_count} | 开始: {start_time}")

    print("╚══════════════════════════════════════╝")


def cmd_week():
    """本周周报"""
    progress = get_progress()
    print(generate_week_report(progress))


def cmd_init():
    """初始化配置"""
    print("""
╔══════════════════════════════════════════════════╗
║          🚀 AI Study CLI 初始化设置               ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  本工具支持:                                      ║
║  🤖 Telegram推送 (推荐)                           ║
║  📱 微信推送 (PushPlus)                           ║
║  🐦 飞书推送 (自定义机器人)                         ║
║  🐙 GitHub笔记同步                                ║
║  ⏰ 上班倒计时                                    ║
║                                                  ║
╚══════════════════════════════════════════════════╝
""")

    # === 1. Telegram推送（优先推荐）===
    print("═══ 🤖 Telegram推送 (推荐) ═══")
    print("  1. 在Telegram中搜索 @BotFather 创建新Bot")
    print("  2. 获取Bot Token")
    print("  3. 发送 /start 给你的Bot获取 chat_id\n")
    tg_token = input("请输入Telegram Bot Token (直接回车跳过): ").strip()
    tg_chat_id = ""
    if tg_token:
        tg_chat_id = input("请输入Telegram Chat ID: ").strip()

    # === 2. 微信推送 ===
    print("\n═══ 📱 微信推送 (PushPlus) ═══")
    print("  1. 访问 https://www.pushplus.plus/")
    print("  2. 微信扫码关注并登录")
    print("  3. 复制你的 token\n")
    token = input("请输入PushPlus token (直接回车跳过): ").strip()

    # === 3. 飞书推送 ===
    print("\n═══ 🐦 飞书推送 (自定义机器人) ═══")
    print("  1. 打开飞书，创建一个群（或使用已有群）")
    print("  2. 群设置 → 机器人 → 添加机器人 → 自定义机器人")
    print("  3. 输入机器人名称（如: AI学习助手）")
    print("  4. 复制 Webhook 地址")
    print("  5. [可选] 开启签名校验，复制密钥\n")
    feishu_webhook = input("请输入飞书 Webhook URL (直接回车跳过): ").strip()
    feishu_secret = ""
    if feishu_webhook:
        feishu_secret = input("请输入飞书签名密钥 (没有则回车跳过): ").strip()

    # === 4. GitHub 笔记同步 ===
    print("\n═══ 🐙 GitHub 笔记同步 ═══")
    print("  将学习记录推送到你的 GitHub 笔记仓库")
    print("  需要: Personal Access Token (PAT) + 仓库名\n")
    github_token = input("请输入 GitHub PAT (直接回车跳过): ").strip()
    github_repo = ""
    if github_token:
        github_repo = input("请输入笔记仓库 (如 sxvvv/notes): ").strip()

    # === 5. 上班日期 ===
    print("\n═══ ⏰ 上班倒计时 ═══")
    print("  设置上班日期，每天显示倒计时提醒\n")
    job_date = input("请输入上班日期 (格式 YYYY-MM-DD, 回车跳过): ").strip()

    # === 6. 提醒时间 ===
    remind_time = input("\n请输入每日提醒时间 (默认09:00): ").strip() or "09:00"

    # 保存配置
    config = init_config(
        pushplus_token=token,
        remind_time=remind_time,
        feishu_webhook=feishu_webhook,
        feishu_secret=feishu_secret,
        github_token=github_token,
        github_notes_repo=github_repo,
        job_start_date=job_date,
        telegram_bot_token=tg_token,
        telegram_chat_id=tg_chat_id,
    )

    # 打印配置结果
    print(f"\n✅ 配置已保存！")
    print(f"   Telegram:  {'已配置 ✅' if tg_token else '未配置 ⏭️'}")
    print(f"   微信推送:  {'已配置 ✅' if token else '未配置 ⏭️'}")
    print(f"   飞书推送:  {'已配置 ✅' if feishu_webhook else '未配置 ⏭️'}")
    print(f"   GitHub:   {'已配置 ✅' if github_token else '未配置 ⏭️'}")
    print(f"   上班日期:  {job_date if job_date else '未设置'}")
    print(f"   提醒时间:  {remind_time}")

    # 测试推送
    if tg_token:
        print("\n正在测试Telegram推送...")
        ok, msg = push_telegram("🎉 AI Study CLI", "推送配置成功！你的学习助手已准备就绪。")
        print(f"   {'✅' if ok else '❌'} {msg}")

    if token:
        print("\n正在测试微信推送...")
        ok, msg = push_wechat("🎉 AI Study CLI", "推送配置成功！你的学习助手已准备就绪。")
        print(f"   {'✅' if ok else '❌'} {msg}")

    if feishu_webhook:
        print("正在测试飞书推送...")
        ok, msg = push_feishu("🎉 AI Study CLI", "飞书推送配置成功！你的学习助手已准备就绪。")
        print(f"   {'✅' if ok else '❌'} {msg}")

    # 设置定时任务
    print(f"\n正在设置每日定时提醒...")
    result = setup_windows_schedule(remind_time)
    print(result)

    print(f"\n🎉 初始化完成！")
    print(f"   运行 'python study.py today' 开始学习")
    print(f"   运行 'python study.py serve' 启动API服务")
    print(f"   运行 'python study.py bot' 启动Telegram机器人")


def cmd_notify(test=False):
    """发送推送通知（仅Telegram）"""
    if test:
        config = get_config()
        if config.get("telegram_bot_token"):
            ok, msg = push_telegram("🧪 测试推送", "如果你收到这条消息，说明Telegram推送配置正确！")
            print(f"Telegram: {'✅' if ok else '❌'} {msg}")
        else:
            print("❌ 未配置Telegram Bot，请运行 study init 设置")
    else:
        result = send_daily_reminder()
        print(result)


def cmd_remind(time_str="09:00"):
    """设置定时提醒"""
    result = setup_windows_schedule(time_str)
    print(result)

    # 同时更新配置
    config = get_config()
    config["remind_time"] = time_str
    save_config(config)


def cmd_serve():
    """启动FastAPI服务"""
    from api.server import run_server
    print("🚀 启动 API 服务器 (http://localhost:8000)...")
    print("   API文档: http://localhost:8000/docs")
    run_server()


def cmd_bot():
    """启动Telegram机器人"""
    from bot.bot import run_bot
    run_bot()


def cmd_skills():
    """显示JD技能地图"""
    from skillmap import format_skill_map
    print(format_skill_map())


def cmd_stars():
    """显示GitHub starred仓库与技能映射"""
    from github_sync import get_starred_with_skills

    repos, error = get_starred_with_skills()
    if error:
        print(f"❌ {error}")
        return

    if not repos:
        print("📭 没有找到starred仓库")
        return

    print(f"⭐ 共 {len(repos)} 个starred仓库\n")

    matched = [r for r in repos if r["matched_skills"]]
    unmatched = [r for r in repos if not r["matched_skills"]]

    if matched:
        print("━━━ 🎯 已匹配技能 ━━━")
        for r in matched[:15]:
            skills_str = ", ".join(s["name"] for s in r["matched_skills"])
            print(f"  {r['name']}: {skills_str}")
        if len(matched) > 15:
            print(f"  ... 还有 {len(matched) - 15} 个")

    if unmatched:
        print(f"\n━━━ ❓ 未匹配 ({len(unmatched)}个) ━━━")
        for r in unmatched[:5]:
            print(f"  {r['name']}: {r['description'][:60]}...")


def cmd_help():
    """显示帮助"""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower()

    if command == "today":
        cmd_today()
    elif command == "done":
        if len(sys.argv) < 3:
            print("用法: study done <任务ID>")
            print("例如: study done 1-1-1")
            return
        cmd_done(sys.argv[2])
    elif command == "skip":
        if len(sys.argv) < 3:
            print("用法: study skip <任务ID> [原因]")
            return
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        cmd_skip(sys.argv[2], reason)
    elif command == "status":
        cmd_status()
    elif command == "quiz":
        cmd_quiz()
    elif command == "quiz-done":
        if len(sys.argv) < 4:
            print("用法: study quiz-done <题目ID> <understand|fuzzy|not>")
            return
        cmd_quiz_done(sys.argv[2], sys.argv[3])
    elif command == "resources":
        cmd_resources()
    elif command == "add":
        if len(sys.argv) < 3:
            print("用法: study add <url> [标签]")
            return
        url = sys.argv[2]
        tag = sys.argv[3] if len(sys.argv) > 3 else ""
        cmd_add_resource(url, tag)
    elif command == "feed":
        refresh = len(sys.argv) > 2 and sys.argv[2] == "refresh"
        cmd_feed(refresh=refresh)
    elif command == "flash":
        cmd_flash()
    elif command == "flash-answer":
        if len(sys.argv) < 3:
            print("用法: study flash-answer <闪卡ID>")
            return
        cmd_flash_answer(sys.argv[2])
    elif command == "flash-ok":
        if len(sys.argv) < 3:
            print("用法: study flash-ok <闪卡ID>")
            return
        cmd_flash_review(sys.argv[2], True)
    elif command == "flash-fail":
        if len(sys.argv) < 3:
            print("用法: study flash-fail <闪卡ID>")
            return
        cmd_flash_review(sys.argv[2], False)
    elif command == "flash-stats":
        cmd_flash_stats()
    elif command == "note":
        if len(sys.argv) < 4:
            print("用法: study note <主题> <标题>")
            print("主题: triton, llm, nlp, clip, gpu, cuda, inference, rl, daily")
            print("例如: study note triton \"Triton matmul优化\"")
            return
        topic = sys.argv[2]
        title_text = " ".join(sys.argv[3:])
        cmd_note(topic, title_text)
    elif command == "sync":
        cmd_sync()
    elif command == "history":
        cmd_history()
    elif command == "week":
        cmd_week()
    elif command == "init":
        cmd_init()
    elif command == "notify":
        test = len(sys.argv) > 2 and sys.argv[2] == "test"
        evening = len(sys.argv) > 2 and sys.argv[2] == "evening"
        if evening:
            result = send_evening_reminder()
            print(result)
        elif test:
            cmd_notify(test=True)
        else:
            cmd_notify(test=False)
    elif command == "remind":
        time_str = sys.argv[2] if len(sys.argv) > 2 else "09:00"
        cmd_remind(time_str)
    elif command == "refresh":
        cmd_refresh()
    elif command == "project":
        cmd_project()
    elif command == "tutor":
        cmd_tutor()
    elif command == "generate":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else ""
        cmd_generate(subcmd)
    elif command == "serve":
        cmd_serve()
    elif command == "bot":
        cmd_bot()
    elif command == "skills":
        cmd_skills()
    elif command == "stars":
        cmd_stars()
    elif command in ("help", "-h", "--help"):
        cmd_help()
    else:
        print(f"❌ 未知命令: {command}")
        cmd_help()


if __name__ == "__main__":
    main()
