"""在线内容抓取模块 - GitHub Trending / 知乎 / B站"""
import json
import os
import re
from datetime import datetime
from html.parser import HTMLParser

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    pass

from config import DATA_DIR

# AI/ML 相关关键词（用于过滤内容）
AI_KEYWORDS = [
    "llm", "gpt", "transformer", "cuda", "gpu", "inference", "triton",
    "vllm", "rlhf", "rl", "reinforcement", "neural", "deep learning",
    "machine learning", "ai", "model", "training", "fine-tune", "lora",
    "quantization", "attention", "diffusion", "embedding", "tokenizer",
    "pytorch", "tensorflow", "jax", "大模型", "推理", "训练", "微调",
    "量化", "算子", "显卡", "人工智能", "深度学习", "机器学习",
    "自然语言处理", "nlp", "cv", "多模态", "agent", "rag",
    "metax", "maca", "macablas", "macadnn", "沐曦", "国产芯片", "国产gpu",
    "datawhale", "miniMind", "nanovllm",
]


def _get_cache_path(date_str=None):
    """获取当日缓存文件路径"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(DATA_DIR, f"daily_feed_{date_str}.json")


def _load_cache():
    """加载当日缓存"""
    cache_path = _get_cache_path()
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(data):
    """保存当日缓存"""
    cache_path = _get_cache_path()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _fetch_url(url, headers=None, timeout=15):
    """通用 HTTP GET 请求"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    if headers:
        default_headers.update(headers)
    req = Request(url, headers=default_headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return None


def _is_ai_related(text):
    """判断内容是否与 AI/ML 相关"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in AI_KEYWORDS)


# ============== GitHub Trending ==============

class GitHubTrendingParser(HTMLParser):
    """解析 GitHub Trending 页面 HTML"""

    def __init__(self):
        super().__init__()
        self.repos = []
        self._current_repo = {}
        self._in_repo_row = False
        self._in_repo_name = False
        self._in_desc = False
        self._in_lang = False
        self._in_stars = False
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get("class", "")

        if tag == "article" and "Box-row" in cls:
            self._in_repo_row = True
            self._current_repo = {"name": "", "desc": "", "lang": "", "stars": "", "url": ""}

        if self._in_repo_row:
            if tag == "h2" and "lh-condensed" in cls:
                self._in_repo_name = True
            if tag == "a" and self._in_repo_name:
                href = attrs_dict.get("href", "")
                if href:
                    self._current_repo["url"] = "https://github.com" + href
                    self._current_repo["name"] = href.strip("/")
            if tag == "p" and ("col-9" in cls or "my-1" in cls):
                self._in_desc = True
            if tag == "span" and "d-inline-block" in cls and "ml-0" in cls:
                self._in_lang = True
            if tag == "a" and "muted-link" in cls and "mr-3" in cls:
                self._in_stars = True

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self._in_repo_name and "/" in data:
            # repo name in text
            pass
        if self._in_desc:
            self._current_repo["desc"] += data
        if self._in_lang:
            self._current_repo["lang"] = data
        if self._in_stars:
            self._current_repo["stars"] = data

    def handle_endtag(self, tag):
        if tag == "h2" and self._in_repo_name:
            self._in_repo_name = False
        if tag == "p" and self._in_desc:
            self._in_desc = False
        if tag == "span" and self._in_lang:
            self._in_lang = False
        if tag == "a" and self._in_stars:
            self._in_stars = False
        if tag == "article" and self._in_repo_row:
            self._in_repo_row = False
            if self._current_repo.get("name"):
                self.repos.append(self._current_repo)


def fetch_github_trending():
    """抓取 GitHub Trending（所有语言 + Python）"""
    results = []

    for lang in ["", "python"]:
        url = f"https://github.com/trending/{lang}?since=daily"
        html = _fetch_url(url)
        if not html:
            continue

        parser = GitHubTrendingParser()
        try:
            parser.feed(html)
        except Exception:
            continue

        for repo in parser.repos:
            search_text = f"{repo['name']} {repo['desc']}"
            if _is_ai_related(search_text):
                if not any(r["name"] == repo["name"] for r in results):
                    results.append(repo)

    return results[:10]  # 最多10个


# ============== B站热门 ==============

def fetch_bilibili_popular():
    """抓取B站AI相关视频（热门 + 搜索补充）"""
    results = []

    # 1. 先从热门中筛选 AI 相关
    url = "https://api.bilibili.com/x/web-interface/popular?ps=50&pn=1"
    data = _fetch_url(url)
    if data:
        try:
            resp = json.loads(data)
            items = resp.get("data", {}).get("list", [])
            for item in items:
                title = item.get("title", "")
                desc = item.get("desc", "")
                owner = item.get("owner", {}).get("name", "")
                bvid = item.get("bvid", "")
                if _is_ai_related(f"{title} {desc}"):
                    results.append({
                        "title": title,
                        "author": owner,
                        "url": f"https://www.bilibili.com/video/{bvid}",
                        "desc": desc[:100] if desc else "",
                    })
        except (json.JSONDecodeError, KeyError):
            pass

    # 2. 如果热门中AI内容不足，用搜索补充
    if len(results) < 5:
        for keyword in ["AI大模型", "GPU推理", "LLM教程", "CUDA编程"]:
            search_url = f"https://api.bilibili.com/x/web-interface/search/type?search_type=video&keyword={keyword}&order=pubdate&duration=0&page=1"
            data = _fetch_url(search_url)
            if not data:
                continue
            try:
                resp = json.loads(data)
                items = resp.get("data", {}).get("result", [])
                for item in items[:3]:
                    title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                    author = item.get("author", "")
                    bvid = item.get("bvid", "")
                    desc = item.get("description", "")
                    if bvid and not any(r["url"].endswith(bvid) for r in results):
                        results.append({
                            "title": title,
                            "author": author,
                            "url": f"https://www.bilibili.com/video/{bvid}",
                            "desc": desc[:100] if desc else "",
                        })
            except (json.JSONDecodeError, KeyError):
                continue
            if len(results) >= 8:
                break

    return results[:8]


# ============== 知乎热榜 ==============

def fetch_zhihu_hot():
    """抓取知乎热榜中AI相关话题"""
    results = []

    url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
    headers = {"Accept": "application/json"}
    data = _fetch_url(url, headers=headers)
    if not data:
        # 备用：尝试知乎热搜
        return _fetch_zhihu_search_fallback()

    try:
        resp = json.loads(data)
        items = resp.get("data", [])
    except (json.JSONDecodeError, KeyError):
        return results

    for item in items:
        target = item.get("target", {})
        title = target.get("title", "")
        excerpt = target.get("excerpt", "")
        url_token = target.get("id", "")

        if _is_ai_related(f"{title} {excerpt}"):
            results.append({
                "title": title,
                "url": f"https://www.zhihu.com/question/{url_token}",
                "desc": excerpt[:100] if excerpt else "",
            })

    return results[:8]


def _fetch_zhihu_search_fallback():
    """知乎搜索 AI 相关内容（热榜 API 不可用时的备选）"""
    results = []
    for query in ["AI大模型", "GPU推理", "LLM"]:
        url = f"https://www.zhihu.com/api/v4/search_v3?t=general&q={query}&correction=1&offset=0&limit=5"
        data = _fetch_url(url, headers={"Accept": "application/json"})
        if not data:
            continue
        try:
            resp = json.loads(data)
            for item in resp.get("data", []):
                obj = item.get("object", {})
                title = obj.get("title", "")
                if title:
                    # 清理 HTML 标签
                    title = re.sub(r"<[^>]+>", "", title)
                    question_id = obj.get("question", {}).get("id") or obj.get("id", "")
                    results.append({
                        "title": title,
                        "url": f"https://www.zhihu.com/question/{question_id}" if question_id else "",
                        "desc": "",
                    })
        except Exception:
            continue
    return results[:8]


# ============== 聚合接口 ==============

def fetch_daily_recommendations(force_refresh=False):
    """获取今日推荐内容（带缓存）"""
    if not force_refresh:
        cached = _load_cache()
        if cached:
            return cached

    recommendations = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "github": [],
        "bilibili": [],
        "zhihu": [],
    }

    # 并行抓取（实际是串行，但保持零依赖）
    print("  正在获取 GitHub Trending...")
    recommendations["github"] = fetch_github_trending()

    print("  正在获取 B站热门...")
    recommendations["bilibili"] = fetch_bilibili_popular()

    print("  正在获取 知乎热榜...")
    recommendations["zhihu"] = fetch_zhihu_hot()

    _save_cache(recommendations)
    return recommendations


def format_recommendations(data):
    """格式化推荐内容为终端输出"""
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════╗")
    lines.append(f"║           📡 今日AI学习推荐 ({data['date']})              ║")
    lines.append("╠══════════════════════════════════════════════════════════╣")

    # GitHub
    lines.append("║")
    lines.append("║  🐙 GitHub Trending (AI相关)")
    lines.append("║  ─────────────────────────────")
    if data["github"]:
        for i, repo in enumerate(data["github"], 1):
            stars = f" ⭐{repo['stars']}" if repo.get("stars") else ""
            lang = f" [{repo['lang']}]" if repo.get("lang") else ""
            lines.append(f"║  {i}. {repo['name']}{lang}{stars}")
            if repo.get("desc"):
                desc = repo["desc"][:60]
                lines.append(f"║     {desc}")
            lines.append(f"║     {repo['url']}")
    else:
        lines.append("║  (暂无AI相关热门项目)")

    # B站
    lines.append("║")
    lines.append("║  📺 B站热门 (科技/AI)")
    lines.append("║  ─────────────────────────────")
    if data["bilibili"]:
        for i, video in enumerate(data["bilibili"], 1):
            lines.append(f"║  {i}. {video['title']}")
            lines.append(f"║     UP: {video['author']}  {video['url']}")
    else:
        lines.append("║  (暂无AI相关热门视频)")

    # 知乎
    lines.append("║")
    lines.append("║  💬 知乎热榜 (AI相关)")
    lines.append("║  ─────────────────────────────")
    if data["zhihu"]:
        for i, topic in enumerate(data["zhihu"], 1):
            lines.append(f"║  {i}. {topic['title']}")
            if topic.get("url"):
                lines.append(f"║     {topic['url']}")
    else:
        lines.append("║  (暂无AI相关热门话题)")

    lines.append("║")
    lines.append("╚══════════════════════════════════════════════════════════╝")
    return "\n".join(lines)
