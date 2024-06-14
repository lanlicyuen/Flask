from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import os
import requests
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # 从环境变量中读取 SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://my_news:hMscKStCefbMEMaP@localhost/my_news'  # 使用 pymysql 连接到数据库
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 读取API密钥和其他配置
news_api_key = os.getenv('NEWS_API_KEY')
discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

# 初始化调度器
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))
scheduler.start()

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class UserSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    keyword = db.Column(db.String(150), nullable=False)
    send_time = db.Column(db.Time, nullable=False)
    loop = db.Column(db.Boolean, default=False)
    interval = db.Column(db.Integer, default=10)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

latest_news = {}

@app.route('/')
def home():
    return render_template('index.html', news=latest_news)

@app.route('/btc_price')
def btc_price():
    binance_api_url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    response = requests.get(binance_api_url)
    btc_price = None
    if response.status_code == 200:
        data = response.json()
        btc_price = int(float(data['price']))
    return jsonify({'btc_price': btc_price})

@app.route('/latest_news')
def get_latest_news():
    return jsonify(latest_news)

def fetch_latest_news(keyword, api_key):
    url = f'https://newsapi.org/v2/everything?q={keyword}&apiKey={api_key}&pageSize=10&sortBy=publishedAt'
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return [{"title": article["title"], "url": article["url"]} for article in articles]
    else:
        logging.error(f"Failed to fetch news for {keyword}: {response.status_code}")
        return []

def update_news():
    global latest_news
    keywords = ["Bitcoin", "elon musk", "Nvidia", "Fed"]
    news = {}
    for keyword in keywords:
        news[keyword] = fetch_latest_news(keyword, news_api_key)
    latest_news = news

# 初始化时获取最新新闻
update_news()

# 定时任务每小时更新新闻
scheduler.add_job(update_news, 'interval', hours=1)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=82)
