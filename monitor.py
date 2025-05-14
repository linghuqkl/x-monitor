import requests
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time
from pathlib import Path

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

USER_ID_CACHE_FILE = "user_ids.json"

# === 公共函数 ===
def load_user_id_cache():
    if Path(USER_ID_CACHE_FILE).exists():
        with open(USER_ID_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_id_cache(cache):
    with open(USER_ID_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_user_id(username, cache):
    if username in cache:
        return cache[username]

    print(f"🌐 正在从 Twitter 获取 @{username} 的 user_id...")
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 429:
        print(f"⛔ 获取 @{username} 的 user_id 时被限流。")
        return None
    r.raise_for_status()
    user_id = r.json()['data']['id']
    cache[username] = user_id
    save_user_id_cache(cache)
    return user_id

def get_latest_tweets(user_id):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": 5,
        "tweet.fields": "created_at,text"
    }
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    r = requests.get(url, headers=headers, params=params)

    if r.status_code == 429:
        print("⛔ Twitter API 被限流（429 Too Many Requests），请稍后再试。")
        return []

    r.raise_for_status()
    return r.json().get("data", [])

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

def get_alert_record_file(username):
    return Path(f".last_alert_{username}.txt")

def load_last_alerted_ids(username):
    path = get_alert_record_file(username)
    if path.exists():
        return set(path.read_text().splitlines())
    return set()

def save_last_alerted_id(username, tweet_id):
    path = get_alert_record_file(username)
    with open(path, 'a') as f:
        f.write(f"{tweet_id}\n")

def main():
    try:
        user_id_cache = load_user_id_cache()

        for username, keywords in MONITOR_CONFIG.items():
            print(f"\n🔍 正在检查 @{username}...")

            user_id = get_user_id(username, user_id_cache)
            if not user_id:
                print(f"⚠️ 无法获取 @{username} 的 user_id，跳过。")
                continue

            tweets = get_latest_tweets(user_id)
            alerted_ids = load_last_alerted_ids(username)

            for tweet in tweets:
                text = tweet['text']
                tweet_id = tweet['id']

                if tweet_id in alerted_ids:
                    continue

                if any(kw.lower() in text.lower() for kw in keywords):
                    tweet_link = f"https://x.com/{username}/status/{tweet_id}"
                    subject = f"🚨 @{username} 提到关键词"
                    body = f"命中关键词推文：\n\n{text}\n\n🔗 链接：{tweet_link}"
                    send_email(subject, body)
                    save_last_alerted_id(username, tweet_id)
                    print(f"📨 发送提醒：{tweet_link}")
                else:
                    print("📝 无关键词匹配：", text)

            time.sleep(10)

    except Exception as e:
        print("🔥 脚本运行异常：", str(e))

if __name__ == "__main__":
    main()
