"""动态内容生成模块 - 基于模板的quiz/flashcard/resource生成"""
import json
import os
from urllib.parse import quote
from config import DATA_DIR, load_json

GUIDES_DIR = os.path.join(DATA_DIR, "guides")


def _load_templates():
    """加载内容模板"""
    filepath = os.path.join(GUIDES_DIR, "templates.json")
    return load_json(filepath) or {"quiz_templates": [], "flashcard_templates": []}


def generate_quiz_for_task(task_id, task_data):
    """从task数据生成quiz题目

    Args:
        task_id: 如 "1-3-2"
        task_data: task dict, 包含 title, desc, key_points 等
    Returns:
        生成的quiz dict, 或 None
    """
    key_points = task_data.get("key_points", [])
    if not key_points:
        return None

    title = task_data.get("title", "")
    desc = task_data.get("desc", "")

    # 从key_points中提取核心概念
    # 策略：取第一个key_point作为问题素材
    main_point = key_points[0] if key_points else desc

    # 生成问题
    question = f"请解释{title}中的核心概念：{main_point.split('，')[0].split(':')[0]}"
    if len(key_points) > 1:
        hint = f"提示：考虑 {key_points[1][:50]}"
    else:
        hint = f"参考: {desc}"

    tags = task_id.split("-")
    return {
        "id": f"q-auto-{task_id}",
        "after_day": int(tags[1]) if len(tags) > 1 else 1,
        "question": question,
        "hint": hint,
        "tags": [f"auto-generated", task_data.get("type", "read")],
        "auto_generated": True,
    }


def generate_flashcard_from_topic(topic, context=""):
    """从主题生成闪卡模板"""
    templates = _load_templates()
    flash_templates = templates.get("flashcard_templates", [])

    if not flash_templates:
        # 使用默认模板
        flash_templates = [
            {"front_pattern": "什么是{concept}？核心原理是什么？",
             "back_pattern": "{context}"},
            {"front_pattern": "{concept}的关键实现步骤是什么？",
             "back_pattern": "1. {step1}\n2. {step2}\n3. {step3}"},
        ]

    if flash_templates:
        tmpl = flash_templates[0]
        front = tmpl.get("front_pattern", "请解释: {concept}").replace("{concept}", topic)
        back = context if context else f"参考学习资料了解{topic}的详细内容"
        return {
            "id": f"fc-auto-{topic[:20].replace(' ', '-')}",
            "front": front,
            "back": back,
            "topic": topic,
            "source": "auto-generated",
        }
    return None


def generate_resources_from_keywords(keywords):
    """从关键词生成资源搜索链接"""
    resources = []
    for kw in keywords[:3]:
        encoded = quote(kw)
        resources.append({
            "name": f"搜索: {kw}",
            "url": f"https://github.com/search?q={encoded}&type=repositories",
            "auto_generated": True,
        })
    return resources


def generate_missing_quizzes():
    """为没有quiz题的任务自动生成quiz"""
    from content_engine import _load_guide

    quizzes_file = os.path.join(DATA_DIR, "quizzes.json")
    quiz_data = load_json(quizzes_file) or {"quizzes": []}
    existing_ids = {q["id"] for q in quiz_data["quizzes"]}

    # 收集所有已有quiz覆盖的task_id
    covered_tasks = set()
    for q in quiz_data["quizzes"]:
        # 从q-1-01这样的ID无法直接映射task，但after_day可以用来判断覆盖范围
        pass

    new_quizzes = []
    for phase_id in range(1, 7):
        guide = _load_guide(phase_id)
        enrichments = guide.get("enrichments", {})

        for task_id, enrichment in enrichments.items():
            auto_id = f"q-auto-{task_id}"
            if auto_id not in existing_ids:
                quiz = generate_quiz_for_task(task_id, enrichment)
                if quiz:
                    new_quizzes.append(quiz)
                    existing_ids.add(auto_id)

    if new_quizzes:
        quiz_data["quizzes"].extend(new_quizzes)
        with open(quizzes_file, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)

    return len(new_quizzes)


def generate_missing_flashcards():
    """为没有flashcard的任务生成闪卡"""
    from content_engine import _load_guide, generate_flashcards_from_guides

    # 先从guides提取已有flashcards
    count = generate_flashcards_from_guides()
    return count


def get_dynamic_enrichment(task):
    """为没有enrichment的task生成动态内容

    当task既没有自带key_points/resources，也没有guide enrichment时，
    从task的title和desc生成基础内容。
    """
    title = task.get("title", "")
    desc = task.get("desc", "")
    task_id = task.get("id", "")

    if not title:
        return task

    enriched = dict(task)

    # 从desc生成key_points
    if not enriched.get("key_points"):
        points = []
        if desc:
            # 按标点分句作为key_points
            sentences = desc.replace("，", "\n").replace("。", "\n").replace("；", "\n").split("\n")
            points = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5][:4]
        if not points:
            points = [f"理解{title}的核心概念和原理", f"掌握{title}的实现方法"]
        enriched["key_points"] = points

    # 从title生成搜索资源
    if not enriched.get("resources"):
        keywords = title.split()[:3]
        enriched["resources"] = generate_resources_from_keywords(keywords)

    return enriched
