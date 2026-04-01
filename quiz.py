"""知识自测模块 - 支持间隔重复"""
import random
from datetime import datetime, timedelta
from config import QUIZZES_FILE, load_json
from tracker import get_progress, save_progress, get_current_day


def get_quiz_questions(count=3):
    """获取今日自测题目（基于间隔重复）"""
    progress = get_progress()
    current_day = get_current_day(progress)
    quizzes = load_json(QUIZZES_FILE)

    if not quizzes or "quizzes" not in quizzes:
        return [], "题库未找到"

    all_quizzes = quizzes["quizzes"]
    quiz_history = progress.get("quiz_history", [])

    # 筛选当前可用的题目（after_day <= current_day）
    available = [q for q in all_quizzes if q["after_day"] <= current_day]

    if not available:
        return [], "还没有可用的自测题，继续学习吧！"

    # 间隔重复逻辑：优先选择需要复习的题目
    scored = []
    for q in available:
        # 查找该题的历史答题记录
        history = [h for h in quiz_history if h["quiz_id"] == q["id"]]

        if not history:
            # 从未答过的题，高优先级
            scored.append((q, 100))
        else:
            last_record = history[-1]
            last_date = datetime.strptime(last_record["date"], "%Y-%m-%d")
            days_since = (datetime.now() - last_date).days
            confidence = last_record.get("confidence", "fuzzy")

            # 根据上次自评和时间间隔计算复习优先级
            if confidence == "not_understand":
                # 不懂的题，1天后就要复习
                interval = 1
            elif confidence == "fuzzy":
                # 模糊的题，3天后复习
                interval = 3
            else:
                # 理解的题，7天后复习
                interval = 7

            if days_since >= interval:
                # 需要复习了
                scored.append((q, 50 + days_since))
            else:
                # 还不需要复习
                scored.append((q, max(0, days_since - interval)))

    # 按优先级排序，取前count个
    scored.sort(key=lambda x: x[1], reverse=True)
    selected = [item[0] for item in scored[:count]]

    # 如果不够，随机补充
    if len(selected) < count:
        remaining = [q for q in available if q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:count - len(selected)])

    return selected, None


def record_quiz_result(quiz_id, confidence):
    """记录答题结果
    
    Args:
        quiz_id: 题目ID
        confidence: 自评结果 - "understand"(理解), "fuzzy"(模糊), "not_understand"(不会)
    """
    progress = get_progress()

    if "quiz_history" not in progress:
        progress["quiz_history"] = []

    progress["quiz_history"].append({
        "quiz_id": quiz_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "confidence": confidence
    })

    save_progress(progress)


def format_quiz(questions):
    """格式化自测题目输出"""
    if not questions:
        return "暂无可用的自测题"

    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║              🧠 知识自测时间                      ║",
        "║   回答后请自评: 理解 / 模糊 / 不会                ║",
        "╠══════════════════════════════════════════════════╣",
    ]

    for i, q in enumerate(questions, 1):
        lines.append(f"║")
        lines.append(f"║  Q{i}. [{q['id']}] {q['question']}")
        if q.get("hint"):
            lines.append(f"║      💡 提示: {q['hint']}")
        tags_str = " ".join(f"#{t}" for t in q.get("tags", []))
        lines.append(f"║      🏷️ {tags_str}")
        lines.append(f"║")

    lines.extend([
        "╠══════════════════════════════════════════════════╣",
        "║  完成后请运行:                                    ║",
        "║  study quiz-done <题目ID> <understand|fuzzy|not>  ║",
        "╚══════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def get_quiz_stats(progress):
    """获取自测统计"""
    history = progress.get("quiz_history", [])
    if not history:
        return "还没有答过题"

    total = len(history)
    understand = sum(1 for h in history if h["confidence"] == "understand")
    fuzzy = sum(1 for h in history if h["confidence"] == "fuzzy")
    not_understand = sum(1 for h in history if h["confidence"] == "not_understand")

    return (
        f"📊 自测统计: 共答 {total} 题\n"
        f"   ✅ 理解: {understand} ({understand*100//total if total else 0}%)\n"
        f"   🟡 模糊: {fuzzy} ({fuzzy*100//total if total else 0}%)\n"
        f"   ❌ 不会: {not_understand} ({not_understand*100//total if total else 0}%)"
    )
