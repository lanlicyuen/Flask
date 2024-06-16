import os
import requests
import logging
from datetime import datetime
import pytz
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # 从环境变量中读取 SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://my_news:hMscKStCefbMEMaP@localhost/my_news'  # 使用 pymysql 连接到数据库
db = SQLAlchemy(app)

# 读取API密钥
news_api_key = os.getenv('NEWS_API_KEY')

# 数据库模型
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

def fetch_latest_news(keyword, api_key):
    url = f'https://newsapi.org/v2/everything?q={keyword}&apiKey={api_key}&pageSize=10&sortBy=publishedAt'
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return [{"title": article["title"], "url": article["url"], "published_at": article["publishedAt"]} for article in articles]
    else:
        logging.error(f"Failed to fetch news for {keyword}: {response.status_code}")
        return []

def update_news():
    keywords = ["Bitcoin", "elon musk", "Nvidia", "Fed"]
    with app.app_context():
        for keyword in keywords:
            articles = fetch_latest_news(keyword, news_api_key)
            for article in articles:
                news_record = News(
                    keyword=keyword,
                    title=article["title"],
                    url=article["url"],
                    published_at=datetime.strptime(article["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Shanghai'))
                )
                db.session.add(news_record)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_news()
