"""资料库管理模块"""
from config import RESOURCES_FILE, CUSTOM_RESOURCES_FILE, load_json, save_json
from tracker import get_current_day, get_progress, get_phase_info


def get_phase_resources(phase_id=None):
    """获取指定阶段的推荐资料"""
    if phase_id is None:
        progress = get_progress()
        current_day = get_current_day(progress)
        phase_info = get_phase_info(current_day)
        phase_id = phase_info["phase_id"]

    resources = load_json(RESOURCES_FILE)
    if not resources or "resources" not in resources:
        return "资料库未找到"

    phase_key = f"phase_{phase_id}"
    if phase_key not in resources["resources"]:
        return f"阶段{phase_id}暂无推荐资料"

    phase_data = resources["resources"][phase_key]
    custom = _get_custom_for_phase(phase_id)

    lines = [
        f"╔══════════════════════════════════════════════════╗",
        f"║  📚 阶段{phase_id}: {phase_data['name']}",
        f"╠══════════════════════════════════════════════════╣",
    ]

    # 按优先级分组
    must_read = [m for m in phase_data["materials"] if m["priority"] == "必读"]
    recommended = [m for m in phase_data["materials"] if m["priority"] == "推荐"]
    optional = [m for m in phase_data["materials"] if m["priority"] not in ("必读", "推荐")]

    if must_read:
        lines.append("║")
        lines.append("║  🔴 必读:")
        for m in must_read:
            lang_tag = f"[{m['lang'].upper()}]"
            type_tag = f"[{m['type']}]"
            lines.append(f"║    {type_tag} {lang_tag} {m['title']}")
            lines.append(f"║    🔗 {m['url']}")

    if recommended:
        lines.append("║")
        lines.append("║  🟡 推荐:")
        for m in recommended:
            lang_tag = f"[{m['lang'].upper()}]"
            type_tag = f"[{m['type']}]"
            lines.append(f"║    {type_tag} {lang_tag} {m['title']}")
            lines.append(f"║    🔗 {m['url']}")

    if optional:
        lines.append("║")
        lines.append("║  🟢 选读:")
        for m in optional:
            lang_tag = f"[{m['lang'].upper()}]"
            type_tag = f"[{m['type']}]"
            lines.append(f"║    {type_tag} {lang_tag} {m['title']}")
            lines.append(f"║    🔗 {m['url']}")

    if custom:
        lines.append("║")
        lines.append("║  📌 我的收藏:")
        for m in custom:
            lines.append(f"║    [{m.get('tag', '未分类')}] {m.get('title', m['url'])}")
            lines.append(f"║    🔗 {m['url']}")

    lines.extend([
        "║",
        "╚══════════════════════════════════════════════════╝",
    ])

    return "\n".join(lines)


def add_custom_resource(url, tag="", title=""):
    """添加自定义资料"""
    custom = load_json(CUSTOM_RESOURCES_FILE)
    if not custom:
        custom = {"resources": []}

    progress = get_progress()
    current_day = get_current_day(progress)
    phase_info = get_phase_info(current_day)

    entry = {
        "url": url,
        "tag": tag or "未分类",
        "title": title or url,
        "phase": phase_info["phase_id"],
        "added_date": __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    }

    custom["resources"].append(entry)
    save_json(CUSTOM_RESOURCES_FILE, custom)
    return f"✅ 资料已添加: {url} [#{tag}]"


def _get_custom_for_phase(phase_id):
    """获取某阶段的自定义资料"""
    custom = load_json(CUSTOM_RESOURCES_FILE)
    if not custom or "resources" not in custom:
        return []
    return [r for r in custom["resources"] if r.get("phase") == phase_id]
