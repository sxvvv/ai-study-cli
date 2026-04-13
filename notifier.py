"""推送通知模块 - Telegram + PushPlus微信推送 + 飞书推送 + Windows Toast"""
import os
import sys
import json
import subprocess
import hmac
import hashlib
import base64
import time
from datetime import datetime

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    pass

from config import get_config


def push_telegram(title, content, parse_mode=None):
    """通过Telegram Bot推送消息

    Args:
        title: 消息标题
        content: 消息内容
        parse_mode: 解析模式 HTML/Markdown/None
    """
    config = get_config()
    token = config.get("telegram_bot_token", "")
    chat_id = config.get("telegram_chat_id", "")

    if not token or not chat_id:
        return False, "未配置Telegram Bot token或chat_id，请运行 study init 设置"

    # 清理内容：移除可能导致HTML解析失败的字符
    import re
    clean_content = content.replace("━", "=").replace("═", "=").replace("╔", "[").replace("╗", "]")
    clean_content = clean_content.replace("╚", "[").replace("╝", "]").replace("╠", "[").replace("╣", "]")
    clean_content = clean_content.replace("║", "|").replace("┃", "|")
    clean_content = re.sub(r'[^\x00-\xFFFF]', '', clean_content)

    text = f"*{title}*\n\n{clean_content}"
    # Telegram消息长度限制4096
    if len(text) > 4000:
        text = text[:4000] + "\n\n..."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
    }).encode("utf-8")

    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                return True, "Telegram推送成功！"
            else:
                return False, f"推送失败: {result.get('description', '未知错误')}"
    except Exception as e:
        return False, f"Telegram推送请求失败: {str(e)}"


def push_wechat(title, content):
    """通过PushPlus推送消息到微信
    
    PushPlus文档: https://www.pushplus.plus/doc/
    免费版每天200条，完全够用
    """
    config = get_config()
    token = config.get("pushplus_token", "")

    if not token:
        return False, "未配置PushPlus token，请运行 study init 设置"

    url = "http://www.pushplus.plus/send"
    data = json.dumps({
        "token": token,
        "title": title,
        "content": content,
        "template": "txt"  # 纯文本格式
    }).encode("utf-8")

    req = Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("code") == 200:
                return True, "微信推送成功！"
            else:
                return False, f"推送失败: {result.get('msg', '未知错误')}"
    except Exception as e:
        return False, f"推送请求失败: {str(e)}"


def _gen_feishu_sign(secret):
    """生成飞书机器人签名"""
    timestamp = str(int(time.time()))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")
    return timestamp, sign


def push_feishu(title, content):
    """通过飞书自定义机器人推送消息

    飞书文档: https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot
    """
    config = get_config()
    webhook = config.get("feishu_webhook", "")

    if not webhook:
        return False, "未配置飞书 webhook，请运行 study init 设置"

    # 构建富文本消息
    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[
                        {"tag": "text", "text": content}
                    ]]
                }
            }
        }
    }

    # 如果配置了签名密钥
    secret = config.get("feishu_secret", "")
    if secret:
        timestamp, sign = _gen_feishu_sign(secret)
        data["timestamp"] = timestamp
        data["sign"] = sign

    body = json.dumps(data).encode("utf-8")
    req = Request(webhook, data=body, headers={"Content-Type": "application/json; charset=utf-8"})

    try:
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                return True, "飞书推送成功！"
            else:
                return False, f"飞书推送失败: {result.get('msg', result.get('StatusMessage', '未知错误'))}"
    except Exception as e:
        return False, f"飞书推送请求失败: {str(e)}"


def push_windows_toast(title, message):
    """Windows Toast通知（仅Windows系统）"""
    if sys.platform != "win32":
        return False, "非Windows系统，跳过Toast通知"

    try:
        # 使用PowerShell发送Toast通知
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

        $template = @"
        <toast>
            <visual>
                <binding template="ToastGeneric">
                    <text>{title}</text>
                    <text>{message}</text>
                </binding>
            </visual>
        </toast>
"@

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AI Study CLI").Show($toast)
        '''
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=5
        )
        return True, "Toast通知已发送"
    except Exception as e:
        # 回退方案：使用msg命令
        try:
            subprocess.run(
                ["msg", "*", f"{title}\n\n{message}"],
                capture_output=True, timeout=5
            )
            return True, "通知已发送(msg)"
        except Exception:
            return False, f"通知发送失败: {str(e)}"


def send_daily_reminder():
    """发送每日学习提醒（Telegram + 微信 + 飞书 + Windows通知）"""
    from planner import get_today_summary_for_push
    from tracker import get_progress, get_current_day, check_micro_achieved

    progress = get_progress()
    current_day = get_current_day(progress)
    micro_done = check_micro_achieved(progress)

    title = f"📚 AI学习提醒 - {datetime.now().strftime('%m月%d日')}"
    content = get_today_summary_for_push()

    # 逼输出提醒: 如果今天还没做任何学习活动
    if not micro_done:
        today_str = datetime.now().strftime("%Y-%m-%d")
        log = progress.get("daily_logs", {}).get(today_str, {})
        has_output = bool(log.get("completed"))
        if not has_output:
            content += "\n\n⚠️ 今天还没有任何学习记录！"
            content += "\n💡 最低门槛: 答3道quiz 或 复习5张闪卡"
            content += "\n   运行: study quiz 或 study flash"

    results = []

    # Telegram推送（仅Telegram）
    config = get_config()
    if config.get("telegram_bot_token"):
        ok, msg = push_telegram(title, content)
        results.append(f"Telegram: {'✅' if ok else '❌'} {msg}")
    else:
        results.append("❌ 未配置Telegram Bot，请运行 study init 设置")

    return "\n".join(results)


def send_evening_reminder():
    """晚间提醒：逼输出 — 检查今日是否完成学习+输出"""
    from tracker import get_progress, get_current_day, check_micro_achieved
    from planner import get_today_summary_for_push

    progress = get_progress()
    current_day = get_current_day(progress)
    micro_done = check_micro_achieved(progress)
    today_str = datetime.now().strftime("%Y-%m-%d")
    log = progress.get("daily_logs", {}).get(today_str, {})
    completed = log.get("completed", [])

    if micro_done and len(completed) >= 2:
        # 今天做得不错，鼓励一下
        title = "🎉 今日学习达标！"
        content = f"今日已完成 {len(completed)} 个任务，micro已达成！\n"
        content += "别忘了: study sync 推送总结到 GitHub"
        content += "\n坚持就是胜利！明天继续💪"
    else:
        # 需要督促
        title = "⚠️ 今日学习提醒"
        content = f"今天还没有完成学习任务！\n\n"
        content += "📌 最低门槛（5分钟）:\n"
        content += "  study quiz — 答3道题\n"
        content += "  study flash — 复习5张闪卡\n\n"
        content += "💪 完成今日计划:\n"
        content += "  study today — 查看今日任务\n"
        content += "  study done <ID> — 标记完成\n\n"
        content += "📝 记得输出:\n"
        content += "  study sync — 推送总结到GitHub\n"
        content += f"🔥 当前连续: {progress.get('streak', 0)} 天，别断！"

    results = []
    config = get_config()
    if config.get("telegram_bot_token"):
        ok, msg = push_telegram(title, content)
        results.append(f"Telegram: {'✅' if ok else '❌'} {msg}")
    else:
        results.append("❌ 未配置Telegram Bot，请运行 study init 设置")

    return "\n".join(results)


def setup_windows_schedule(time_str="09:00", evening_time="21:00"):
    """设置Windows计划任务，每天定时提醒

    Args:
        time_str: 早晨提醒时间，格式 "HH:MM"
        evening_time: 晚间提醒时间，格式 "HH:MM"
    """
    if sys.platform != "win32":
        return _generate_cron_hint(time_str)

    # 获取当前脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable
    study_script = os.path.join(script_dir, "study.py")

    results = []

    # 早晨提醒
    morning_task = "AIStudyCLI_DailyReminder"
    cmd = (
        f'schtasks /create /tn "{morning_task}" '
        f'/tr "\\"{python_exe}\\" \\"{study_script}\\" notify" '
        f'/sc daily /st {time_str} /f'
    )
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            results.append(f"✅ 早晨提醒: 每天 {time_str}")
        else:
            results.append(f"❌ 早晨提醒设置失败: {result.stderr}")
    except Exception as e:
        results.append(f"❌ 早晨提醒设置失败: {str(e)}")

    # 晚间提醒（逼输出）
    evening_task = "AIStudyCLI_EveningReminder"
    cmd = (
        f'schtasks /create /tn "{evening_task}" '
        f'/tr "\\"{python_exe}\\" \\"{study_script}\\" notify evening" '
        f'/sc daily /st {evening_time} /f'
    )
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            results.append(f"✅ 晚间提醒: 每天 {evening_time} (督促输出)")
        else:
            results.append(f"❌ 晚间提醒设置失败: {result.stderr}")
    except Exception as e:
        results.append(f"❌ 晚间提醒设置失败: {str(e)}")

    results.append(f"\n如需修改: study remind {time_str}")
    results.append(f"如需删除: schtasks /delete /tn \"{morning_task}\" /f")
    results.append(f"          schtasks /delete /tn \"{evening_task}\" /f")

    return "\n".join(results)


def _generate_cron_hint(time_str):
    """为非Windows系统生成cron提示"""
    hour, minute = time_str.split(":")
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "study.py"))
    python_path = sys.executable

    return (
        f"请添加以下crontab条目 (运行 crontab -e):\n\n"
        f"{minute} {hour} * * * cd {os.path.dirname(script_path)} && {python_path} {script_path} notify\n"
    )
