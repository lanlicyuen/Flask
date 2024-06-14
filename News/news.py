from flask import Flask, request, jsonify
import os
import requests
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # 从环境变量中读取 SECRET_KEY
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://my_news:hMscKStCefbMEMaP@localhost/my_news'  # 使用 pymysql 连接到数据库
db = SQLAlchemy(app)

# 读取API密钥和其他配置
news_api_key = os.getenv('NEWS_API_KEY')
discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

# 初始化调度器
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))
scheduler.start()


# 数据库模型
class UserSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    keyword = db.Column(db.String(150), nullable=False)
    send_time = db.Column(db.Time, nullable=False)
    loop = db.Column(db.Boolean, default=False)
    interval = db.Column(db.Integer, default=10)


@app.route('/index')
@login_required
def index():
    settings = UserSetting.query.filter_by(user_id=current_user.id).all()
    preset_stocks = [setting.keyword for setting in settings]
    send_time = settings[0].send_time.strftime('%H:%M') if settings else ''
    loop = settings[0].loop if settings else False
    interval = settings[0].interval if settings else 10
    return render_template('send_news.html', preset_stocks=preset_stocks, send_time=send_time, loop=loop,
                           interval=interval)


@app.route('/save_settings', methods=['POST'])
@login_required
def save_settings():
    data = request.get_json()
    keywords = data.get('keywords', [])
    send_time_str = data.get('send_time', '')
    loop = data.get('loop', False)
    interval = data.get('interval', 10)

    send_time = datetime.strptime(send_time_str, '%H:%M').time()

    # 清除旧设置
    UserSetting.query.filter_by(user_id=current_user.id).delete()

    # 保存新设置
    for keyword in keywords:
        setting = UserSetting(user_id=current_user.id, keyword=keyword, send_time=send_time, loop=loop,
                              interval=interval)
        db.session.add(setting)
    db.session.commit()

    return "Settings saved successfully"


@app.route('/send_news', methods=['POST'])
@login_required
def send_news():
    data = request.get_json()
    stocks = data.get('stocks', [])
    if send_news_to_discord(stocks, news_api_key, discord_webhook_url):
        return "Message sent successfully to Discord!"
    else:
        return "Failed to send message to Discord.", 500


@app.route('/start_query', methods=['POST'])
@login_required
def start_query():
    data = request.get_json()
    stocks = data.get('stocks', [])
    news_results = []
    for stock in stocks:
        news = fetch_latest_news(stock, news_api_key)
        news_results.append({"stock": stock, "articles": news})
    return jsonify(news_results)


@app.route('/schedule_send', methods=['POST'])
@login_required
def schedule_send():
    data = request.get_json()
    stocks = data.get('stocks', [])
    send_time_str = data.get('time', '')
    loop = data.get('loop', False)
    interval = data.get('interval', 10)

    if not send_time_str and not loop:
        return "Invalid time format", 400

    if interval < 10:
        return "Interval must be at least 10 minutes", 400

    send_time = None
    if send_time_str:
        try:
            send_time = datetime.strptime(send_time_str, '%H:%M').time()
        except ValueError:
            return "Invalid time format", 400

    def send_scheduled_news():
        send_news_to_discord(stocks, news_api_key, discord_webhook_url)

    # 计划任务
    if loop:
        if send_time:
            start_time = datetime.now(pytz.timezone('Asia/Shanghai')).replace(hour=send_time.hour,
                                                                              minute=send_time.minute, second=0,
                                                                              microsecond=0)
            if start_time < datetime.now(pytz.timezone('Asia/Shanghai')):
                start_time += timedelta(days=1)
            scheduler.add_job(send_scheduled_news, 'interval', minutes=interval, start_date=start_time)
        else:
            scheduler.add_job(send_scheduled_news, 'interval', minutes=interval)
    else:
        if send_time:
            scheduler.add_job(send_scheduled_news, 'cron', hour=send_time.hour, minute=send_time.minute,
                              timezone=pytz.timezone('Asia/Shanghai'))
        else:
            return "Invalid time format", 400

    return "News scheduled to be sent to Discord at the specified time."


def fetch_latest_news(stock, api_key):
    url = f'https://newsapi.org/v2/everything?q={stock}&apiKey={api_key}&pageSize=10&sortBy=publishedAt'
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return [{"title": article["title"], "url": article["url"]} for article in articles]
    else:
        logging.error(f"Failed to fetch news for {stock}: {response.status_code}")
        return []


def send_news_to_discord(stocks, api_key, webhook_url):
    messages = []
    for stock in stocks:
        news = fetch_latest_news(stock, api_key)
        if news:
            message = f"News for {stock}:\n" + "\n".join([f"{article['title']}: {article['url']}" for article in news])
            messages.append(message)

    for message in messages:
        data = {"content": message}
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204:
            logging.error(f"Failed to send message to Discord: {response.status_code}, {response.text}")
            return False
    return True


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=82)
