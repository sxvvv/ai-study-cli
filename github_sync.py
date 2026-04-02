"""GitHub 笔记同步模块 - 推送学习记录到 GitHub"""
import json
import base64
from datetime import datetime

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    pass

from config import get_config

# 学习阶段到笔记目录的映射
PHASE_DIR_MAP = {
    1: "llm-basics",
    2: "triton",
    3: "inference",
    4: "inference-framework",
    5: "rl-training",
    6: "metax-maca",
}

# 支持的自定义主题目录
TOPIC_ALIASES = {
    "triton": "Triton",
    "llm": "llm_paper_note",
    "nlp": "nlp-notes",
    "clip": "clip基础",
    "gpu": "Triton",
    "cuda": "Triton",
    "inference": "inference",
    "rl": "rl-training",
    "daily": "daily",
}


def _github_api(path, method="GET", data=None):
    """GitHub REST API 通用请求"""
    config = get_config()
    token = config.get("github_token", "")
    repo = config.get("github_notes_repo", "")

    if not token or not repo:
        return None, "未配置 GitHub token 或 notes 仓库，请运行 study init 设置"

    url = f"https://api.github.com/repos/{repo}/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Study-CLI",
    }

    if data:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        body = None

    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result, None
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        try:
            error_json = json.loads(error_body)
            msg = error_json.get("message", str(e))
        except Exception:
            msg = str(e)
        return None, f"GitHub API 错误 ({e.code}): {msg}"
    except Exception as e:
        return None, f"请求失败: {str(e)}"


def get_repo_tree():
    """获取仓库目录结构"""
    result, error = _github_api("git/trees/main?recursive=1")
    if error:
        return None, error

    tree = result.get("tree", [])
    dirs = set()
    for item in tree:
        if item["type"] == "tree":
            dirs.add(item["path"])
    return sorted(dirs), None


def _get_file_sha(file_path):
    """获取文件当前 SHA（用于更新已存在的文件）"""
    result, error = _github_api(f"contents/{file_path}")
    if error:
        return None
    return result.get("sha")


def sync_note(topic_dir, filename, content, commit_msg=None):
    """推送或更新笔记文件到 GitHub

    Args:
        topic_dir: 目标目录（如 "Triton", "nlp-notes"）
        filename: 文件名（如 "08_xxx.md"）
        content: 文件内容（字符串）
        commit_msg: 提交信息（可选）
    """
    file_path = f"{topic_dir}/{filename}"

    if not commit_msg:
        commit_msg = f"docs: {filename} - {datetime.now().strftime('%Y-%m-%d')}"

    # Base64 编码内容
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": commit_msg,
        "content": content_b64,
    }

    # 检查文件是否已存在，如果是则需要 SHA
    sha = _get_file_sha(file_path)
    if sha:
        data["sha"] = sha

    result, error = _github_api(f"contents/{file_path}", method="PUT", data=data)
    if error:
        return False, error

    html_url = result.get("content", {}).get("html_url", "")
    return True, f"已推送到 GitHub: {html_url}"


def resolve_topic_dir(topic):
    """解析用户输入的主题到实际目录名"""
    topic_lower = topic.lower()

    # 精确匹配别名
    if topic_lower in TOPIC_ALIASES:
        return TOPIC_ALIASES[topic_lower]

    # 尝试匹配仓库中已有目录
    dirs, error = get_repo_tree()
    if dirs:
        for d in dirs:
            if topic_lower in d.lower():
                return d

    # 用原名创建新目录
    return topic


def generate_daily_summary(progress, current_day, phase_info):
    """生成今日学习总结（Markdown 格式，包含知识点）"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    day_log = progress.get("daily_logs", {}).get(today_str, {})
    completed = day_log.get("completed", [])
    skipped = day_log.get("skipped", [])

    # 尝试获取课程中的任务详情
    from config import CURRICULUM_FILE, load_json
    curriculum = load_json(CURRICULUM_FILE)
    task_details = {}
    if curriculum:
        for phase in curriculum.get("phases", []):
            for task_day in phase.get("tasks", []):
                if task_day.get("day") == current_day:
                    for task in task_day.get("infra", []) + task_day.get("algo", []):
                        task_details[task["id"]] = task
                    break

    lines = [
        f"# Day {current_day} 学习总结 ({today_str})",
        "",
        f"**阶段**: {phase_info.get('phase_name', '开放学习')}",
        f"**连续学习**: {progress.get('streak', 0)} 天",
        "",
    ]

    # 完成的任务 — 包含具体知识点
    if completed:
        lines.append("## 今日完成")
        lines.append("")
        for tid in completed:
            task = task_details.get(tid, {})
            title = task.get("title", tid)
            lines.append(f"### {title}")
            lines.append("")
            if task.get("desc"):
                lines.append(f"> {task['desc']}")
                lines.append("")
            if task.get("key_points"):
                lines.append("**学习要点:**")
                lines.append("")
                for kp in task["key_points"]:
                    lines.append(f"- {kp}")
                lines.append("")
            if task.get("resources"):
                lines.append("**参考资料:**")
                lines.append("")
                for res in task["resources"]:
                    lines.append(f"- [{res['name']}]({res['url']})")
                lines.append("")
    else:
        lines.extend(["## 今日完成", "", "- 今日暂无完成任务", ""])

    # 闪卡复习情况
    try:
        from flashcard import get_flashcard_stats
        fc_stats = get_flashcard_stats()
        if fc_stats["total"] > 0:
            bc = fc_stats["box_counts"]
            lines.extend([
                "## 闪卡复习",
                "",
                f"- 总计: {fc_stats['total']} 张",
                f"- 已掌握: {fc_stats['mastered']} 张",
                f"- 盒子分布: 盒1({bc[1]}) 盒2({bc[2]}) 盒3({bc[3]}) 盒4({bc[4]}) 盒5({bc[5]})",
                "",
            ])
    except Exception:
        pass

    if skipped:
        lines.append("## 跳过的任务")
        lines.append("")
        for s in skipped:
            if isinstance(s, dict):
                lines.append(f"- `{s.get('task_id', '')}` — {s.get('reason', '无原因')}")
            else:
                lines.append(f"- `{s}`")
        lines.append("")

    lines.extend(["---", f"*Generated by AI Study CLI on {today_str}*"])
    return "\n".join(lines)


def sync_daily_summary(progress, current_day, phase_info):
    """推送今日学习总结到 GitHub"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    content = generate_daily_summary(progress, current_day, phase_info)
    filename = f"{today_str}.md"
    commit_msg = f"daily: Day {current_day} 学习总结 ({today_str})"

    return sync_note("daily", filename, content, commit_msg)
