"""
Telegram Bot - AI Study CLI 交互式学习助手

功能:
- 每日推送学习任务
- 交互式Quiz (inline keyboard)
- 闪卡复习 (inline keyboard)
- 连胜查看
- 技能缺口查询
- GitHub仓库映射技能
- DeepSeek AI 费曼检验对话
"""
import os
import sys
import json
import logging

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    pass

# Windows 终端编码修复
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 确保项目根目录在path中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    JobQueue, ContextTypes, MessageHandler, filters,
)

from config import get_config
from tracker import (
    get_progress, start_if_needed, get_current_day,
    record_streak_layer, check_micro_achieved,
)
from planner import get_today_tasks, get_today_summary_for_push
from quiz import get_quiz_questions, record_quiz_result
from flashcard import get_due_cards, review_card, find_card
from skillmap import (
    get_skill_gaps, get_skill_progress_summary,
    map_repo_to_skill, format_skill_map, update_skill_level,
)
from notifier import push_telegram

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def call_deepseek(messages, max_tokens=500):
    """调用DeepSeek API（兼容OpenAI格式）"""
    config = get_config()
    api_key = config.get("deepseek_api_key", "")
    model = config.get("deepseek_model", "deepseek-reasoner")

    if not api_key:
        return None, "未配置DeepSeek API Key"

    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })

    try:
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"]["content"]
            return content, None
    except Exception as e:
        return None, str(e)


def _get_bot_config():
    config = get_config()
    return config.get("telegram_bot_token", ""), config.get("telegram_chat_id", "")


# === Command Handlers ===

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令"""
    keyboard = [
        [InlineKeyboardButton("📋 今日任务", callback_data="today"),
         InlineKeyboardButton("🔥 连胜", callback_data="streak")],
        [InlineKeyboardButton("🧠 Quiz", callback_data="quiz"),
         InlineKeyboardButton("🃏 闪卡", callback_data="flash")],
        [InlineKeyboardButton("🎓 AI导师", callback_data="learn"),
         InlineKeyboardButton("📝 费曼检验", callback_data="feynman")],
        [InlineKeyboardButton("🎯 技能地图", callback_data="skills"),
         InlineKeyboardButton("🔴 缺口", callback_data="gaps")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎓 AI Study CLI 学习助手\n\n"
        "你的JD驱动学习系统已就绪！\n"
        "选择下方按钮开始学习：",
        reply_markup=reply_markup,
    )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """今日任务"""
    output, error = get_today_tasks()
    if error:
        await update.message.reply_text(error)
    else:
        # Telegram消息长度限制
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (内容过长，使用 /skills 查看技能缺口)"
        await update.message.reply_text(output, parse_mode="HTML")


async def cmd_streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """连胜查看"""
    progress = get_progress()
    progress = start_if_needed(progress)
    streak = progress.get("streak", 0)
    max_streak = progress.get("max_streak", 0)
    layer = progress.get("streak_layer", "none")
    micro_done = check_micro_achieved(progress)

    layer_labels = {"micro": "最低门槛✅", "plan": "计划完成🏆", "demo": "技能验证🎯", "none": "未完成"}

    text = (
        f"🔥 <b>连胜状态</b>\n\n"
        f"当前连胜: <b>{streak}天</b>\n"
        f"最长连胜: {max_streak}天\n"
        f"今日层级: {layer_labels.get(layer, layer)}\n"
        f"今日micro: {'✅ 已达成' if micro_done else '❌ 未达成'}\n\n"
        f"💡 完成micro (3道quiz/5张闪卡) 维持连胜！"
    )

    keyboard = []
    if not micro_done:
        keyboard.append([
            InlineKeyboardButton("🧠 做Quiz维持连胜", callback_data="quiz"),
            InlineKeyboardButton("🃏 复习闪卡", callback_data="flash"),
        ])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始Quiz"""
    questions, error = get_quiz_questions(3)
    if error or not questions:
        await update.message.reply_text(error or "暂无可用的quiz题")
        return

    for i, q in enumerate(questions):
        text = f"Q{i+1}. [{q['id']}] {q['question']}"
        if q.get("hint"):
            text += f"\n💡 提示: {q['hint']}"

        keyboard = [
            [
                InlineKeyboardButton("✅ 理解", callback_data=f"quiz:{q['id']}:understand"),
                InlineKeyboardButton("🟡 模糊", callback_data=f"quiz:{q['id']}:fuzzy"),
                InlineKeyboardButton("❌ 不会", callback_data=f"quiz:{q['id']}:not_understand"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)


async def cmd_flash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """闪卡复习"""
    count = 5
    if context.args and context.args[0].isdigit():
        count = min(int(context.args[0]), 10)

    cards = get_due_cards(count)
    if not cards:
        await update.message.reply_text("🎉 今日没有待复习的闪卡！")
        return

    await update.message.reply_text(f"🃏 今日待复习: {len(cards)} 张闪卡")

    for card in cards[:3]:  # Telegram限制，一次最多3张
        text = f"📂 {card.get('topic', '')} | {card.get('day', '')}\n\n❓ {card['front']}"
        keyboard = [
            [
                InlineKeyboardButton("👀 看答案", callback_data=f"flip:{card['id']}"),
            ]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """技能地图"""
    text = format_skill_map()
    if len(text) > 4000:
        text = text[:4000] + "\n\n..."
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_gaps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """技能缺口"""
    gaps = get_skill_gaps()
    if not gaps:
        await update.message.reply_text("🎉 所有技能已达标！")
        return

    lines = ["🔴 <b>技能缺口 Top 10</b>\n"]
    for g in gaps[:10]:
        tag = "必备" if g["jd_relevance"] == "must-have" else "加分"
        bar = "█" * g["current_level"] + "░" * (g["gap"])
        lines.append(f"[{tag}] {g['name']}: [{bar}] {g['current_level']}/{g['max_level']}")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_feynman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """费曼检验：用你自己的话讲出来，Bot像老师一样追问纠错"""
    progress = get_progress()
    progress = start_if_needed(progress)
    current_day = get_current_day(progress)

    # 读取今日任务的key_points作为考核素材
    _, error = get_today_tasks()
    from config import load_json, CURRICULUM_FILE
    curriculum = load_json(CURRICULUM_FILE)

    # 找到今天的任务
    today_keypoints = []
    today_titles = []
    for phase in curriculum.get("phases", []):
        for task in phase.get("tasks", []):
            if task.get("day") == current_day:
                for item in task.get("infra", []):
                    if item.get("key_points"):
                        today_keypoints.extend(item["key_points"])
                    if item.get("title"):
                        today_titles.append(item["title"])

    if not today_keypoints:
        await update.message.reply_text("今天没有可检验的知识点，先去学习吧！\n运行 study today 查看任务")
        return

    # 随机选一个知识点让你讲
    import random
    target = random.choice(today_keypoints)

    # 保存当前检验状态
    config = get_config()
    config["feynman_active"] = True
    config["feynman_target"] = target
    config["feynman_round"] = 0
    from config import save_config
    save_config(config)

    text = (
        "🎓 <b>费曼检验模式</b>\n\n"
        "用你自己的话解释以下概念：\n\n"
        f"📌 {target}\n\n"
        "💡 提示：假装你在给一个完全不懂的人讲清楚\n"
        "直接回复你的解释，我会追问和纠错\n\n"
        "输入 /stop 结束检验"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI导师模式：像教小孩一样逐步引导学习"""
    progress = get_progress()
    progress = start_if_needed(progress)
    current_day = get_current_day(progress)

    # 加载课程和资源
    from config import load_json, CURRICULUM_FILE, DATA_DIR
    import os
    curriculum = load_json(CURRICULUM_FILE)
    resources_file = os.path.join(DATA_DIR, "learning_resources.json")
    resources = load_json(resources_file)

    # 找到今天的任务
    today_titles = []
    today_keypoints = []
    phase_name = ""
    for phase in curriculum.get("phases", []):
        for task in phase.get("tasks", []):
            if task.get("day") == current_day:
                phase_name = phase.get("name", "")
                for item in task.get("infra", []):
                    if item.get("title"):
                        today_titles.append(item["title"])
                    if item.get("key_points"):
                        today_keypoints.extend(item["key_points"])

    if not today_titles:
        await update.message.reply_text("今天没有学习任务，休息一下吧！")
        return

    # 获取对应day的资源
    day_key = f"day{min(current_day, 4)}"
    day_resources = resources.get(day_key, {})

    # 用DeepSeek生成学习引导
    titles_text = "\n".join(f"  - {t}" for t in today_titles)
    resources_text = ""
    if day_resources.get("core_papers"):
        resources_text += "\n核心论文:\n"
        for p in day_resources["core_papers"][:3]:
            resources_text += f"  - {p['name']}: {p['key_idea']}\n"
    if day_resources.get("blogger_resources"):
        resources_text += "\n推荐博主文章:\n"
        for b in day_resources["blogger_resources"]:
            resources_text += f"  - {b['name']}: {b['focus']}\n"

    messages = [
        {"role": "system", "content": (
            "你是一个友善的AI学习导师，像教小朋友一样引导学生学习AI技术。\n"
            "规则：\n"
            "1. 先问学生'你之前了解过这个领域吗？'了解基础水平\n"
            "2. 根据回答调整讲解深度：零基础→用比喻解释，有基础→直接讲核心\n"
            "3. 每次只讲一个知识点，讲完让学生用自己的话复述\n"
            "4. 用中文回复，简洁有趣，控制在300字以内\n"
            "5. 给出今天的学习路线图（3-5步）\n"
            f"今天主题: {phase_name}\n"
            f"要覆盖的lecture:\n{titles_text}\n"
            f"关键知识点: {'; '.join(today_keypoints[:5])}\n"
            f"{resources_text}"
        )},
        {"role": "user", "content": "老师好，我准备好学今天的内容了！"}
    ]

    wait_msg = await update.message.reply_text("🎓 AI导师正在准备今日课程...")

    ai_reply, err = call_deepseek(messages, max_tokens=800)

    if err:
        await wait_msg.edit_text(f"❌ AI调用失败: {err}\n\n先用 /today 查看今日任务")
        return

    # 保存学习对话状态
    config = get_config()
    config["learn_active"] = True
    config["learn_day"] = current_day
    config["learn_round"] = 0
    config["learn_keypoints"] = today_keypoints
    from config import save_config
    save_config(config)

    text = (
        f"🎓 <b>AI导师模式启动</b> (Day {current_day})\n\n"
        f"{ai_reply}\n\n"
        f"💡 直接回复和导师对话\n"
        f"/feynman — 随时检验知识点\n"
        f"/stop — 退出导师模式"
    )

    try:
        await wait_msg.edit_text(text, parse_mode="HTML")
    except Exception:
        await wait_msg.edit_text(text)


async def cmd_stop_feynman(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """停止费曼检验/导师模式"""
    config = get_config()
    from config import save_config

    stopped = []
    if config.get("feynman_active"):
        config["feynman_active"] = False
        stopped.append("费曼检验")
    if config.get("learn_active"):
        config["learn_active"] = False
        stopped.append("AI导师")

    if not stopped:
        await update.message.reply_text("当前没有进行中的模式")
        return

    save_config(config)
    await update.message.reply_text(f"✅ 已退出: {'、'.join(stopped)}\n\n/today 查看任务 /learn 重新开始学习")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理普通文本消息 — DeepSeek AI对话（导师模式+费曼检验）"""
    config = get_config()
    user_text = update.message.text

    # 导师模式对话
    if config.get("learn_active"):
        current_day = config.get("learn_day", 1)
        learn_round = config.get("learn_round", 0) + 1
        keypoints = config.get("learn_keypoints", [])

        from config import load_json, CURRICULUM_FILE, DATA_DIR
        import os
        curriculum = load_json(CURRICULUM_FILE)
        resources_file = os.path.join(DATA_DIR, "learning_resources.json")
        resources = load_json(resources_file)
        day_key = f"day{min(current_day, 4)}"
        day_resources = resources.get(day_key, {})

        system_prompt = (
            "你是一个友善严格的AI学习导师，正在和学生进行AI知识对话。\n"
            "规则：\n"
            "1. 学生说了什么，你要判断理解是否正确\n"
            "2. 正确→鼓励并引导下一个知识点；错误→温和纠正\n"
            "3. 适时追问，让学生用自己的话解释概念\n"
            "4. 控制在200字以内，简洁有力\n"
            f"今天剩余知识点: {'; '.join(keypoints[:10])}\n"
            f"这是第{learn_round}轮对话"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]

        wait_msg = await update.message.reply_text("🤔 导师思考中...")
        ai_reply, err = call_deepseek(messages)
        if err:
            await wait_msg.edit_text(f"❌ AI调用失败: {err}")
            return

        from config import save_config
        config["learn_round"] = learn_round
        save_config(config)

        try:
            await wait_msg.edit_text(ai_reply, parse_mode="HTML")
        except Exception:
            await wait_msg.edit_text(ai_reply)
        return

    # 费曼检验对话
    if config.get("feynman_active"):
        target = config.get("feynman_target", "")
        round_num = config.get("feynman_round", 0)

        round_num += 1

        # 构建prompt让DeepSeek当老师
        system_prompt = (
            "你是一个严格但友善的AI学习导师。学生正在学习AI Infra相关知识。\n"
            "你的任务是：\n"
            "1. 评估学生对概念的解释是否准确、完整\n"
            "2. 如果有不准确的地方，指出并纠正\n"
            "3. 如果有遗漏，追问让学生补充\n"
            "4. 用简洁的中文回复，不超过200字\n"
            "5. 如果学生理解到位（覆盖了核心概念且没有明显错误），说'通过'\n\n"
            f"标准知识点: {target}\n\n"
            f"这是第{round_num}/3轮对话。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"我的理解是: {user_text}"},
        ]

        # 发送"思考中..."
        thinking_msg = await update.message.reply_text("🤔 DeepSeek正在评估你的理解...")

        ai_reply, err = call_deepseek(messages)

        if err:
            await thinking_msg.edit_text(f"❌ AI调用失败: {err}")
            return

        from config import save_config

        # 判断是否通过
        passed = "通过" in ai_reply or "✅" in ai_reply

        if passed or round_num >= 3:
            config["feynman_active"] = False
            save_config(config)

            if passed:
                result = record_streak_layer("micro")
                progress = get_progress()
                streak = progress.get("streak", 0)
                reply = f"{ai_reply}\n\n{result} (🔥{streak}天)\n\n再来一个？ /feynman"
            else:
                reply = (
                    f"📚 <b>三轮结束</b>\n\n"
                    f"AI评价:\n{ai_reply}\n\n"
                    f"📌 标准知识点: {target}\n\n"
                    f"💡 回去重看lecture，再来 /feynman"
                )
        else:
            config["feynman_round"] = round_num
            save_config(config)
            reply = f"{ai_reply}\n\n(第{round_num}/3轮 | /stop 放弃)"

        try:
            await thinking_msg.edit_text(reply, parse_mode="HTML")
        except Exception:
            await thinking_msg.edit_text(reply)


async def cmd_map_repo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """映射GitHub仓库到技能 /map_repo vllm-project/vllm"""
    if not context.args:
        await update.message.reply_text("用法: /map_repo <repo_name>\n例如: /map_repo vllm-project/vllm")
        return

    repo = context.args[0]
    skills = map_repo_to_skill(repo)

    if not skills:
        await update.message.reply_text(f"未找到与 {repo} 匹配的技能")
        return

    lines = [f"📦 <b>{repo}</b> 映射到以下技能:\n"]
    for s in skills:
        lines.append(f"• {s['name']} ({s['jd_relevance']})")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# === Callback Handlers ===

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理inline keyboard回调"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("quiz:"):
        # quiz:{id}:{confidence}
        parts = data.split(":")
        if len(parts) == 3:
            _, quiz_id, confidence = parts
            record_quiz_result(quiz_id, confidence)
            labels = {"understand": "✅ 理解", "fuzzy": "🟡 模糊", "not_understand": "❌ 不会"}

            # 记录micro达成
            result = record_streak_layer("micro")

            progress = get_progress()
            streak = progress.get("streak", 0)
            await query.edit_message_text(
                f"{labels.get(confidence, confidence)} — {quiz_id}\n\n{result} (🔥{streak}天)"
            )

    elif data.startswith("flip:"):
        # flip:{card_id} — 显示答案
        card_id = data.split(":")[1]
        card = find_card(card_id)
        if card:
            text = f"💡 {card['back']}"
            if card.get("source"):
                text += f"\n\n📖 参考: {card['source']}"
            keyboard = [
                [
                    InlineKeyboardButton("✅ 记住了", callback_data=f"fc:{card_id}:ok"),
                    InlineKeyboardButton("❌ 没记住", callback_data=f"fc:{card_id}:fail"),
                ]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("fc:"):
        # fc:{card_id}:{ok|fail}
        parts = data.split(":")
        if len(parts) == 3:
            _, card_id, result_str = parts
            remembered = result_str == "ok"
            result = review_card(card_id, remembered)

            # 记录micro达成
            streak_result = record_streak_layer("micro")

            progress = get_progress()
            streak = progress.get("streak", 0)
            await query.edit_message_text(f"{result}\n\n{streak_result} (🔥{streak}天)")

    elif data == "today":
        output, error = get_today_tasks()
        await query.edit_message_text(error or output, parse_mode="HTML")

    elif data == "streak":
        progress = get_progress()
        progress = start_if_needed(progress)
        streak = progress.get("streak", 0)
        micro_done = check_micro_achieved(progress)
        await query.edit_message_text(
            f"🔥 当前连胜: {streak}天\n今日micro: {'✅' if micro_done else '❌'}",
            parse_mode="HTML",
        )

    elif data == "quiz":
        questions, error = get_quiz_questions(3)
        if error or not questions:
            await query.edit_message_text(error or "暂无quiz")
            return
        for q in questions[:1]:  # 简化，一次一题
            text = f"❓ {q['question']}"
            keyboard = [[
                InlineKeyboardButton("✅", callback_data=f"quiz:{q['id']}:understand"),
                InlineKeyboardButton("🟡", callback_data=f"quiz:{q['id']}:fuzzy"),
                InlineKeyboardButton("❌", callback_data=f"quiz:{q['id']}:not_understand"),
            ]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "flash":
        cards = get_due_cards(3)
        if not cards:
            await query.edit_message_text("🎉 今日没有待复习的闪卡")
            return
        card = cards[0]
        text = f"❓ {card['front']}"
        keyboard = [[InlineKeyboardButton("👀 看答案", callback_data=f"flip:{card['id']}")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "skills":
        text = format_skill_map()
        if len(text) > 4000:
            text = text[:4000]
        await query.edit_message_text(text, parse_mode="HTML")

    elif data == "gaps":
        gaps = get_skill_gaps()
        if not gaps:
            await query.edit_message_text("🎉 所有技能已达标！")
            return
        lines = [f"🔴 缺口 Top 5:"]
        for g in gaps[:5]:
            lines.append(f"• {g['name']} ({g['current_level']}/{g['max_level']})")
        await query.edit_message_text("\n".join(lines))

    elif data == "learn":
        # 触发AI导师模式
        fake_update = type('obj', (object,), {
            'message': type('obj', (object,), {
                'reply_text': query.message.reply_text,
                'edit_text': query.edit_message_text,
            })()
        })()
        await cmd_learn(fake_update, context)

    elif data == "feynman":
        await cmd_feynman(update, context)


# === Daily Push Job ===

async def daily_push(context: ContextTypes.DEFAULT_TYPE):
    """每日定时推送"""
    content = get_today_summary_for_push()
    title = "📚 今日AI学习任务"

    config = get_config()
    chat_id = config.get("telegram_chat_id", "")
    if chat_id:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"<b>{title}</b>\n\n{content}",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Daily push failed: {e}")


def run_bot():
    """启动Telegram Bot"""
    token, chat_id = _get_bot_config()

    if not token:
        print("❌ 未配置 telegram_bot_token，请运行 study init 设置")
        return

    application = Application.builder().token(token).build()

    # 注册命令
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("today", cmd_today))
    application.add_handler(CommandHandler("streak", cmd_streak))
    application.add_handler(CommandHandler("quiz", cmd_quiz))
    application.add_handler(CommandHandler("flash", cmd_flash))
    application.add_handler(CommandHandler("skills", cmd_skills))
    application.add_handler(CommandHandler("gaps", cmd_gaps))
    application.add_handler(CommandHandler("map_repo", cmd_map_repo))
    application.add_handler(CommandHandler("feynman", cmd_feynman))
    application.add_handler(CommandHandler("learn", cmd_learn))
    application.add_handler(CommandHandler("stop", cmd_stop_feynman))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 定时推送
    config = get_config()
    remind_time = config.get("remind_time", "09:00")
    hour, minute = map(int, remind_time.split(":"))

    job_queue = application.job_queue
    job_queue.run_daily(daily_push, time=__import__("datetime").time(hour, minute))

    print(f"🤖 Telegram Bot 启动！每日推送时间: {remind_time}")
    print(f"   命令: /start /today /quiz /flash /streak /skills /gaps /map_repo /learn /feynman")

    application.run_polling()


if __name__ == "__main__":
    run_bot()
