import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

TWITTER_BEARER_TOKEN = os.environ['TWITTER_BEARER_TOKEN']
EMAIL_FROM = os.environ['EMAIL_FROM']
EMAIL_TO = os.environ['EMAIL_TO']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
TWITTER_USERNAME = 'humafinance'
KEYWORD = 'deposits'

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
    r.raise_for_status()
    return r.json().get("data", [])

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtpllib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    user_id = get_user_id(TWITTER_USERNAME)
    tweets = get_latest_tweets(user_id)
    for tweet in tweets:
        if KEYWORD.lower() in tweet['text'].lower():
            tweet_link = f"https://x.com/{TWITTER_USERNAME}/status/{tweet['id']}"
            send_email("🚨 Huma 提到 deposits", f"{tweet['text']}\n\n{tweet_link}")
            break

if __name__ == "__main__":
    main()
