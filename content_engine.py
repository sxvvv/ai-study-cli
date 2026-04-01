"""内容引擎 - 课程骨架 + 动态丰富层合并"""
import os
import json
from config import DATA_DIR, load_json

GUIDES_DIR = os.path.join(DATA_DIR, "guides")


def _load_guide(phase_id):
    """加载某个阶段的 guide 文件"""
    phase_names = {
        1: "phase1_llm_basics",
        2: "phase2_gpu_programming",
        3: "phase3_inference_engine",
        4: "phase4_build_framework",
        5: "phase5_rl_training",
        6: "phase6_domestic_gpu",
    }
    filename = phase_names.get(phase_id, "")
    if not filename:
        return {}
    filepath = os.path.join(GUIDES_DIR, f"{filename}.json")
    return load_json(filepath) or {}


def load_enrichment(task_id):
    """根据 task_id 加载丰富内容

    task_id 格式: {phase}-{day_in_phase}-{task_num}，如 "1-3-2"
    """
    try:
        phase_id = int(task_id.split("-")[0])
    except (ValueError, IndexError):
        return {}

    guide = _load_guide(phase_id)
    enrichments = guide.get("enrichments", {})
    return enrichments.get(task_id, {})


def merge_task_with_enrichment(task):
    """合并课程骨架任务和丰富层内容

    优先使用 task 自带的 key_points/resources（向后兼容），
    否则从 guides/ 加载。
    """
    task_id = task.get("id", "")

    # 如果任务本身已有丰富内容，直接返回
    if task.get("key_points") and task.get("resources"):
        return task

    enrichment = load_enrichment(task_id)
    if not enrichment:
        return task

    # 合并：task 自带的优先
    merged = dict(task)
    if not merged.get("key_points"):
        merged["key_points"] = enrichment.get("key_points", [])
    if not merged.get("resources"):
        merged["resources"] = enrichment.get("resources", [])
    return merged


def get_enriched_day_tasks(day_tasks):
    """对一天的所有任务进行丰富"""
    enriched = dict(day_tasks)
    enriched["infra"] = [merge_task_with_enrichment(t) for t in day_tasks.get("infra", [])]
    enriched["algo"] = [merge_task_with_enrichment(t) for t in day_tasks.get("algo", [])]
    return enriched


def generate_flashcards_from_guides():
    """从所有 guide 文件提取闪卡，写入 flashcards.json"""
    from flashcard import _load_flashcards, _save_flashcards

    all_cards = []
    seen_ids = set()

    # 从6个Phase的guide中提取
    for phase_id in range(1, 7):
        guide = _load_guide(phase_id)
        enrichments = guide.get("enrichments", {})

        for task_id, enrichment in enrichments.items():
            for fc in enrichment.get("flashcards", []):
                card_id = fc.get("id", "")
                if card_id and card_id not in seen_ids:
                    seen_ids.add(card_id)
                    card = {
                        "id": card_id,
                        "front": fc.get("front", ""),
                        "back": fc.get("back", ""),
                        "topic": fc.get("topic", ""),
                        "day": fc.get("day", ""),
                        "source": fc.get("source", ""),
                        "code": fc.get("code", ""),
                    }
                    all_cards.append(card)

    # 保留已有的非guide闪卡（手动添加的）
    existing = _load_flashcards()
    for card in existing.get("cards", []):
        if card["id"] not in seen_ids:
            all_cards.append(card)
            seen_ids.add(card["id"])

    _save_flashcards({"cards": all_cards})
    return len(all_cards)


def load_open_topics():
    """加载持续学习主题库（Day 85+）"""
    filepath = os.path.join(GUIDES_DIR, "open_topics.json")
    return load_json(filepath) or {"topics": []}


def get_open_mode_daily(current_day):
    """获取开放模式下的每日推荐主题"""
    topics_data = load_open_topics()
    topics = topics_data.get("topics", [])
    if not topics:
        return None

    # 循环轮转主题
    extra_day = current_day - 84  # Day 85 → 1, Day 86 → 2, ...
    idx = (extra_day - 1) % len(topics)
    return topics[idx]
