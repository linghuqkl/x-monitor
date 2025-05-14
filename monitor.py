import requests
import smtplib
import json
import os
import subprocess
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === 配置 ===
TWITTER_BEARER_TOKEN = os.environ['TWITTER_BEARER_TOKEN']
EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_TO = os.environ['EMAIL_TO']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

# === 多账号 + 多关键词配置 ===
MONITOR_CONFIG = {
    "humafinance": ["chuk", "deposits"],
    "Fox2goeth": ["test", "空投"]
}

ALERT_HISTORY_FILE = "sent_alerts.json"

# === 获取 User ID ===
def get_user_id(username):
    print(f"🌐 正在从 Twitter 获取 @{username} 的 user_id...")
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()['data']['id']

# === 获取推文 ===
def get_latest_tweets(user_id):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {"max_results": 5, "tweet.fields": "created_at,text"}
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("data", [])

# === 邮件发送 ===
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

# === 提醒记录 ===
def load_alert_history():
    if Path(ALERT_HISTORY_FILE).exists():
        with open(ALERT_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_alert_history(alerts):
    with open(ALERT_HISTORY_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)

def add_to_alert_history(username, tweet_id, alerts):
    alerts.setdefault(username, []).append(tweet_id)
    save_alert_history(alerts)

def commit_file_update(filename, message):
    subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions[bot]'])
    subprocess.run(['git', 'config', '--global', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'])
    subprocess.run(['git', 'add', filename])
    subprocess.run(['git', 'commit', '-m', message])
    subprocess.run(['git', 'push'])

# === 主逻辑 ===
def main():
    try:
        alert_history = load_alert_history()

        for username, keywords in MONITOR_CONFIG.items():
            print(f"\n🔍 正在检查 @{username}...")

            try:
                user_id = get_user_id(username)
            except Exception as e:
                print(f"❌ 获取 @{username} 的 user_id 失败：{e}")
                continue

            try:
                tweets = get_latest_tweets(user_id)
            except Exception as e:
                print(f"❌ 获取 @{username} 的推文失败：{e}")
                continue

            alerted_ids = set(alert_history.get(username, []))

            for tweet in tweets:
                text = tweet['text']
                tweet_id = tweet['id']

                if tweet_id in alerted_ids:
                    continue

                if any(kw.lower() in text.lower() for kw in keywords):
                    tweet_link = f"https://x.com/{username}/status/{tweet_id}"
                    subject = f"🚨 @{username} 提到关键词"
                    body = f"命中关键词的推文：\n\n{text}\n\n🔗 链接：{tweet_link}"
                    send_email(subject, body)
                    add_to_alert_history(username, tweet_id, alert_history)
                    print(f"📨 发送提醒: {tweet_link}")
                else:
                    print("📝 无关键词匹配: ", text)

        commit_file_update(ALERT_HISTORY_FILE, "更新提醒记录")

    except Exception as e:
        print("🔥 脚本异常: ", str(e))

if __name__ == "__main__":
    main()
