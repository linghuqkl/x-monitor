import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# === 配置 ===
TWITTER_BEARER_TOKEN = os.environ['TWITTER_BEARER_TOKEN']
EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_TO = os.environ['EMAIL_TO']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
TWITTER_USERNAME = 'humafinance'
KEYWORD = 'chuk'  # 当前测试关键词

def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()['data']['id']

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

def main():
    try:
        user_id = get_user_id(TWITTER_USERNAME)
        tweets = get_latest_tweets(user_id)

        for tweet in tweets:
            print("📝 检查推文内容：", tweet['text'])
            if KEYWORD.lower() in tweet['text'].lower():
                tweet_link = f"https://x.com/{TWITTER_USERNAME}/status/{tweet['id']}"
                send_email("🚨 Huma 提到关键词！", f"{tweet['text']}\n\n链接：{tweet_link}")
                break
        else:
            print("🔍 本次扫描未发现包含关键词的推文。")
    except Exception as e:
        print("🔥 脚本执行出错：", str(e))

if __name__ == "__main__":
    main()
