"""闪卡系统 - Leitner间隔复习"""
import json
import os
import random
from datetime import datetime, timedelta

from config import DATA_DIR, load_json, save_json

FLASHCARDS_FILE = os.path.join(DATA_DIR, "flashcards.json")
FLASHCARD_PROGRESS_FILE = os.path.join(DATA_DIR, "flashcard_progress.json")

# Leitner 盒子间隔（天数）
LEITNER_INTERVALS = {
    1: 0,    # 盒子1: 每天复习
    2: 1,    # 盒子2: 隔1天
    3: 3,    # 盒子3: 隔3天
    4: 7,    # 盒子4: 隔7天
    5: 14,   # 盒子5: 隔14天（已掌握）
}


def _load_flashcards():
    """加载闪卡库"""
    return load_json(FLASHCARDS_FILE) or {"cards": []}


def _save_flashcards(data):
    """保存闪卡库"""
    save_json(FLASHCARDS_FILE, data)


def _load_fc_progress():
    """加载闪卡学习进度"""
    return load_json(FLASHCARD_PROGRESS_FILE) or {"card_states": {}}


def _save_fc_progress(data):
    """保存闪卡学习进度"""
    save_json(FLASHCARD_PROGRESS_FILE, data)


def get_due_cards(count=5):
    """获取今日待复习的闪卡"""
    cards_data = _load_flashcards()
    progress = _load_fc_progress()
    today = datetime.now().date()

    due = []
    new = []

    for card in cards_data.get("cards", []):
        card_id = card["id"]
        state = progress["card_states"].get(card_id)

        if not state:
            # 新卡片
            new.append(card)
        else:
            box = state.get("box", 1)
            last_review = datetime.strptime(state["last_review"], "%Y-%m-%d").date()
            interval = LEITNER_INTERVALS.get(box, 14)
            next_review = last_review + timedelta(days=interval)

            if today >= next_review:
                card["_box"] = box
                due.append(card)

    # 优先复习旧卡，再加新卡
    due.sort(key=lambda c: c.get("_box", 1))
    result = due[:count]
    remaining = count - len(result)
    if remaining > 0:
        result.extend(new[:remaining])

    return result


def review_card(card_id, remembered):
    """记录闪卡复习结果

    Args:
        card_id: 闪卡ID
        remembered: True=记住了, False=没记住
    """
    progress = _load_fc_progress()
    today_str = datetime.now().strftime("%Y-%m-%d")

    state = progress["card_states"].get(card_id, {
        "box": 1,
        "last_review": today_str,
        "total_reviews": 0,
        "correct": 0,
    })

    state["total_reviews"] += 1
    state["last_review"] = today_str

    if remembered:
        state["correct"] += 1
        # 升一个盒子（最多到5）
        state["box"] = min(state.get("box", 1) + 1, 5)
    else:
        # 打回盒子1
        state["box"] = 1

    progress["card_states"][card_id] = state
    _save_fc_progress(progress)

    box = state["box"]
    interval = LEITNER_INTERVALS.get(box, 14)
    if remembered:
        if box >= 5:
            return f"✅ 已掌握！下次复习: {interval}天后"
        return f"✅ 正确！升到盒子{box}，下次复习: {interval}天后"
    else:
        return f"❌ 没记住，回到盒子1，明天再复习"


def format_card_front(card):
    """格式化闪卡正面（问题）"""
    lines = [
        "╔══════════════════════════════════════════════════╗",
        f"║  🃏 闪卡 [{card['id']}]",
        f"║  📂 {card.get('topic', '')} | {card.get('day', '')}",
        "╠══════════════════════════════════════════════════╣",
        "║",
    ]
    # 问题可能有多行
    for line in card["front"].split("\n"):
        lines.append(f"║  ❓ {line}")
    lines.extend([
        "║",
        "╠══════════════════════════════════════════════════╣",
        "║  输入 study flash-answer <ID> 查看答案",
        "╚══════════════════════════════════════════════════╝",
    ])
    return "\n".join(lines)


def format_card_back(card):
    """格式化闪卡反面（答案）"""
    lines = [
        "╔══════════════════════════════════════════════════╗",
        f"║  🃏 闪卡答案 [{card['id']}]",
        "╠══════════════════════════════════════════════════╣",
        "║",
    ]
    for line in card["back"].split("\n"):
        lines.append(f"║  💡 {line}")

    if card.get("source"):
        lines.append("║")
        lines.append(f"║  📖 参考: {card['source']}")

    if card.get("code"):
        lines.append("║")
        lines.append("║  📝 关键代码:")
        for line in card["code"].split("\n"):
            lines.append(f"║    {line}")

    lines.extend([
        "║",
        "╠══════════════════════════════════════════════════╣",
        f"║  记住了？  study flash-ok {card['id']}",
        f"║  没记住？  study flash-fail {card['id']}",
        "╚══════════════════════════════════════════════════╝",
    ])
    return "\n".join(lines)


def get_flashcard_stats():
    """获取闪卡统计"""
    cards_data = _load_flashcards()
    progress = _load_fc_progress()

    total = len(cards_data.get("cards", []))
    states = progress.get("card_states", {})
    reviewed = len(states)
    new_count = total - reviewed

    box_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for state in states.values():
        box = state.get("box", 1)
        box_counts[box] = box_counts.get(box, 0) + 1

    mastered = box_counts.get(5, 0)

    return {
        "total": total,
        "new": new_count,
        "mastered": mastered,
        "box_counts": box_counts,
    }


def format_flashcard_stats():
    """格式化闪卡统计"""
    stats = get_flashcard_stats()
    bc = stats["box_counts"]
    lines = [
        f"🃏 闪卡总数: {stats['total']} | 新卡: {stats['new']} | 已掌握: {stats['mastered']}",
        f"   盒子分布: ❶{bc[1]} ❷{bc[2]} ❸{bc[3]} ❹{bc[4]} ❺{bc[5]}",
    ]
    return "\n".join(lines)


def add_flashcard(card_id, front, back, topic="", day="", source="", code=""):
    """添加一张闪卡"""
    data = _load_flashcards()
    # 检查是否已存在
    for c in data["cards"]:
        if c["id"] == card_id:
            return False, f"闪卡 {card_id} 已存在"

    data["cards"].append({
        "id": card_id,
        "front": front,
        "back": back,
        "topic": topic,
        "day": day,
        "source": source,
        "code": code,
    })
    _save_flashcards(data)
    return True, f"闪卡 {card_id} 已添加"


def find_card(card_id):
    """按 ID 查找闪卡"""
    data = _load_flashcards()
    for card in data.get("cards", []):
        if card["id"] == card_id:
            return card
    return None
