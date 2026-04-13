"""配置管理模块"""
import json
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 数据文件路径
CURRICULUM_FILE = os.path.join(DATA_DIR, "curriculum.json")
RESOURCES_FILE = os.path.join(DATA_DIR, "resources.json")
QUIZZES_FILE = os.path.join(DATA_DIR, "quizzes.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
CUSTOM_RESOURCES_FILE = os.path.join(DATA_DIR, "custom.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def load_json(filepath):
    """加载JSON文件"""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    """保存JSON文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_config():
    """获取用户配置"""
    return load_json(CONFIG_FILE)


def save_config(config):
    """保存用户配置"""
    save_json(CONFIG_FILE, config)


def init_config(pushplus_token=None, remind_time="09:00", feishu_webhook=None,
                feishu_secret=None, github_token=None, github_notes_repo=None,
                job_start_date=None, telegram_bot_token=None, telegram_chat_id=None):
    """初始化配置"""
    config = get_config() or {}
    config.update({
        "pushplus_token": pushplus_token or config.get("pushplus_token", ""),
        "remind_time": remind_time or config.get("remind_time", "09:00"),
        "feishu_webhook": feishu_webhook or config.get("feishu_webhook", ""),
        "feishu_secret": feishu_secret or config.get("feishu_secret", ""),
        "github_token": github_token or config.get("github_token", ""),
        "github_notes_repo": github_notes_repo or config.get("github_notes_repo", ""),
        "job_start_date": job_start_date or config.get("job_start_date", ""),
        "telegram_bot_token": telegram_bot_token or config.get("telegram_bot_token", ""),
        "telegram_chat_id": telegram_chat_id or config.get("telegram_chat_id", ""),
        "start_date": config.get("start_date"),
        "initialized": True
    })
    save_config(config)
    return config
