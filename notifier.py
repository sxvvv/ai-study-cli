"""推送通知模块 - PushPlus微信推送 + 飞书推送 + Windows Toast"""
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
    """发送每日学习提醒（同时推微信、飞书和Windows通知）"""
    from planner import get_today_summary_for_push

    title = f"📚 AI学习提醒 - {datetime.now().strftime('%m月%d日')}"
    content = get_today_summary_for_push()

    results = []

    # 微信推送
    ok, msg = push_wechat(title, content)
    results.append(f"微信推送: {'✅' if ok else '❌'} {msg}")

    # 飞书推送
    config = get_config()
    if config.get("feishu_webhook"):
        ok, msg = push_feishu(title, content)
        results.append(f"飞书推送: {'✅' if ok else '❌'} {msg}")

    # Windows Toast
    short_msg = content.split("\n")[0]  # Toast只显示第一行
    ok, msg = push_windows_toast(title, short_msg)
    results.append(f"系统通知: {'✅' if ok else '❌'} {msg}")

    return "\n".join(results)


def setup_windows_schedule(time_str="09:00"):
    """设置Windows计划任务，每天定时提醒
    
    Args:
        time_str: 提醒时间，格式 "HH:MM"
    """
    if sys.platform != "win32":
        return _generate_cron_hint(time_str)

    # 获取当前脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable
    study_script = os.path.join(script_dir, "study.py")

    task_name = "AIStudyCLI_DailyReminder"

    # 创建计划任务的命令
    cmd = (
        f'schtasks /create /tn "{task_name}" '
        f'/tr "\\"{python_exe}\\" \\"{study_script}\\" notify" '
        f'/sc daily /st {time_str} /f'
    )

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return (
                f"✅ 定时提醒已设置！\n"
                f"   任务名: {task_name}\n"
                f"   时间: 每天 {time_str}\n"
                f"   操作: 自动推送今日学习任务到微信\n\n"
                f"   如需修改时间，重新运行: study remind {time_str}\n"
                f"   如需删除，运行: schtasks /delete /tn \"{task_name}\" /f"
            )
        else:
            return (
                f"❌ 设置失败（可能需要管理员权限）\n"
                f"   错误: {result.stderr}\n\n"
                f"   请尝试以管理员身份运行命令行，或手动创建计划任务:\n"
                f"   {cmd}"
            )
    except Exception as e:
        return f"❌ 设置失败: {str(e)}\n\n请手动运行: {cmd}"


def _generate_cron_hint(time_str):
    """为非Windows系统生成cron提示"""
    hour, minute = time_str.split(":")
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "study.py"))
    python_path = sys.executable

    return (
        f"请添加以下crontab条目 (运行 crontab -e):\n\n"
        f"{minute} {hour} * * * cd {os.path.dirname(script_path)} && {python_path} {script_path} notify\n"
    )
