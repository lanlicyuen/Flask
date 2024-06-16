from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import os
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://my_news:hMscKStCefbMEMaP@localhost/my_news'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

class BTCPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    # 从数据库中获取最新的新闻
    news = {}
    keywords = ["Bitcoin", "elon musk", "Nvidia", "Fed"]
    for keyword in keywords:
        news[keyword] = News.query.filter_by(keyword=keyword).order_by(News.published_at.desc()).limit(10).all()
    return render_template('index.html', news=news)

@app.route('/btc_price')
def btc_price():
    binance_api_url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    response = requests.get(binance_api_url)
    btc_price = None
    if response.status_code == 200:
        data = response.json()
        btc_price = float(data['price'])
        # 将价格和当前时间（北京时间）记录到数据库
        beijing_time = datetime.now(pytz.timezone('Asia/Shanghai'))
        btc_record = BTCPrice(price=btc_price, timestamp=beijing_time)
        db.session.add(btc_record)
        db.session.commit()
    else:
        # 如果请求失败，打印错误并返回默认价格
        print(f"Failed to fetch BTC price: {response.status_code}")
        btc_price = 0.0
    return jsonify({'btc_price': btc_price})

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
