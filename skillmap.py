"""JD驱动的技能地图引擎 - 从招聘需求推导学习路径"""
import json
from config import DATA_DIR, load_json, save_json
from tracker import get_progress

SKILLMAP_FILE = f"{DATA_DIR}/skillmap.json"
SKILL_PROGRESS_FILE = f"{DATA_DIR}/skill_progress.json"


def get_skill_map():
    """加载技能地图"""
    data = load_json(SKILLMAP_FILE)
    if not data or "categories" not in data:
        return {"categories": [], "company": "", "role": ""}
    return data


def _load_skill_progress():
    """加载技能学习进度"""
    return load_json(SKILL_PROGRESS_FILE) or {"skills": {}}


def _save_skill_progress(data):
    """保存技能学习进度"""
    save_json(SKILL_PROGRESS_FILE, data)


def get_all_skills():
    """获取扁平化的所有技能列表"""
    skillmap = get_skill_map()
    skills = []
    for cat in skillmap.get("categories", []):
        for skill in cat.get("skills", []):
            skill_copy = dict(skill)
            skill_copy["category_name"] = cat["name"]
            skill_copy["category_id"] = cat["id"]
            skill_copy["jd_relevance"] = cat["jd_relevance"]
            skills.append(skill_copy)
    return skills


def get_skill_by_id(skill_id):
    """按ID查找技能"""
    for skill in get_all_skills():
        if skill["id"] == skill_id:
            return skill
    return None


def get_skill_gaps():
    """获取技能缺口（未达标的技能）"""
    progress = _load_skill_progress()
    skills = get_all_skills()
    gaps = []

    for skill in skills:
        sp = progress["skills"].get(skill["id"], {})
        level = sp.get("level", 0)
        if level < skill["max_level"]:
            gaps.append({
                **skill,
                "current_level": level,
                "gap": skill["max_level"] - level,
            })

    gaps.sort(key=lambda x: (0 if x["jd_relevance"] == "must-have" else 1, -x["gap"]))
    return gaps


def get_skill_progress_summary():
    """获取技能进度摘要"""
    progress = _load_skill_progress()
    skills = get_all_skills()
    must_have = [s for s in skills if s["jd_relevance"] == "must-have"]
    nice_to_have = [s for s in skills if s["jd_relevance"] == "nice-to-have"]

    must_total = sum(s["max_level"] for s in must_have)
    must_done = sum(progress["skills"].get(s["id"], {}).get("level", 0) for s in must_have)
    nice_total = sum(s["max_level"] for s in nice_to_have)
    nice_done = sum(progress["skills"].get(s["id"], {}).get("level", 0) for s in nice_to_have)

    return {
        "must_have": {
            "total": must_total,
            "completed": must_done,
            "percentage": round(must_done / must_total * 100, 1) if must_total else 0,
            "skills": [
                {
                    **s,
                    "current_level": progress["skills"].get(s["id"], {}).get("level", 0),
                }
                for s in must_have
            ],
        },
        "nice_to_have": {
            "total": nice_total,
            "completed": nice_done,
            "percentage": round(nice_done / nice_total * 100, 1) if nice_total else 0,
            "skills": [
                {
                    **s,
                    "current_level": progress["skills"].get(s["id"], {}).get("level", 0),
                }
                for s in nice_to_have
            ],
        },
    }


def update_skill_level(skill_id, level):
    """更新技能等级"""
    progress = _load_skill_progress()
    if "skills" not in progress:
        progress["skills"] = {}

    if skill_id not in progress["skills"]:
        progress["skills"][skill_id] = {}

    progress["skills"][skill_id]["level"] = min(level, 5)
    _save_skill_progress(progress)
    return True


def map_repo_to_skill(repo_name):
    """将GitHub仓库名映射到技能"""
    repo_lower = repo_name.lower()
    skills = get_all_skills()
    matches = []

    for skill in skills:
        score = 0
        # 关键词匹配
        for kw in skill.get("keywords", []):
            if kw in repo_lower:
                score += 3
        # 关联仓库精确匹配
        for related in skill.get("related_repos", []):
            if related.lower() in repo_lower or repo_lower in related.lower():
                score += 10
        if score > 0:
            matches.append({"skill": skill, "score": score})

    matches.sort(key=lambda x: -x["score"])
    return [m["skill"] for m in matches[:3]]


def get_repos_for_skill(skill_id):
    """获取技能关联的GitHub仓库"""
    skill = get_skill_by_id(skill_id)
    if not skill:
        return []
    return skill.get("related_repos", [])


def format_skill_map():
    """格式化技能地图文本输出"""
    summary = get_skill_progress_summary()
    gaps = get_skill_gaps()

    lines = [
        f"🎯 技能地图 — {get_skill_map().get('company', '')} {get_skill_map().get('role', '')}",
        "",
        f"━━━ ✅ 必备技能 ({summary['must_have']['percentage']}%) ━━━",
    ]

    for s in summary["must_have"]["skills"]:
        level = s["current_level"]
        max_l = s["max_level"]
        bar = "█" * level + "░" * (max_l - level)
        lines.append(f"  {s['name']}: [{bar}] {level}/{max_l}")

    lines.append(f"\n━━━ ⭐ 加分技能 ({summary['nice_to_have']['percentage']}%) ━━━")

    for s in summary["nice_to_have"]["skills"]:
        level = s["current_level"]
        max_l = s["max_level"]
        bar = "█" * level + "░" * (max_l - level)
        lines.append(f"  {s['name']}: [{bar}] {level}/{max_l}")

    if gaps:
        top_gaps = gaps[:5]
        lines.append(f"\n━━━ 🔴 最大缺口 (Top 5) ━━━")
        for g in top_gaps:
            tag = "必备" if g["jd_relevance"] == "must-have" else "加分"
            lines.append(f"  [{tag}] {g['name']} — 差{g['gap']}级 (当前{g['current_level']}/{g['max_level']})")

    return "\n".join(lines)
