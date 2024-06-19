from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, Response
import os
import requests
from datetime import datetime, timedelta
import pytz
import json
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import plotly
import plotly.graph_objs as go
import pandas as pd
from decimal import Decimal
from sqlalchemy.types import DECIMAL

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

class BTCPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    price = db.Column(DECIMAL(10, 2), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/btc_price')
def btc_price():
    binance_api_url = 'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    response = requests.get(binance_api_url)
    btc_price = None
    if response.status_code == 200:
        data = response.json()
        btc_price = Decimal(data['price']).quantize(Decimal('0.01'))
        # 将价格和当前时间（北京时间）记录到数据库
        beijing_time = datetime.now(pytz.timezone('Asia/Shanghai'))
        btc_record = BTCPrice(price=btc_price, timestamp=beijing_time)
        db.session.add(btc_record)
        db.session.commit()
    else:
        # 如果请求失败，打印错误并返回默认价格
        print(f"Failed to fetch BTC price: {response.status_code}")
        btc_price = Decimal(0.0).quantize(Decimal('0.01'))
    return jsonify({'btc_price': float(btc_price)})

@app.route('/btc_price_chart_data')
def btc_price_chart_data():
    interval = request.args.get('interval', '1min')
    intervals = {
        '1min': timedelta(minutes=1),
        '5min': timedelta(minutes=5),
        '15min': timedelta(minutes=15),
        '30min': timedelta(minutes=30),
        '1hour': timedelta(hours=1),
        '1day': timedelta(days=1)
    }
    if interval not in intervals:
        interval = '1min'

    end_time = datetime.now(pytz.timezone('Asia/Shanghai'))
    start_time = end_time - intervals[interval]

    prices = BTCPrice.query.filter(BTCPrice.timestamp >= start_time).order_by(BTCPrice.timestamp).all()

    data = {
        'timestamp': [price.timestamp for price in prices],
        'price': [float(price.price) for price in prices]
    }

    df = pd.DataFrame(data)
    fig = go.Figure(data=[go.Candlestick(x=df['timestamp'],
                open=df['price'],
                high=df['price'],
                low=df['price'],
                close=df['price'])])
    fig.update_layout(
        title=f'BTC Price ({interval} interval)',
        xaxis_title='Time',
        yaxis_title='Price',
        yaxis=dict(tickformat='f')  # 使用f格式化，不使用千位分隔符
    )
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return Response(graphJSON, mimetype='application/json')



@app.route('/send_chart_to_discord', methods=['POST'])
def send_chart_to_discord():
    webhook_url = request.form.get('webhook_url')
    interval = request.form.get('interval', '1min')
    if not webhook_url:
        webhook_url = 'https://discord.com/api/webhooks/1247795423679217704/PkkTjASXNZ09gsl0KLyfB_hyo8wphjzdjB7z6zjC49Ll-OgSNM7h4DtUC41KIK9Naiuk'

    chart_data_url = url_for('btc_price_chart_data', interval=interval, _external=True)
    response = requests.get(chart_data_url)
    if response.status_code == 200:
        chart_data = response.json()
        fig = plotly.io.from_json(json.dumps(chart_data))
        chart_image = plotly.io.to_image(fig, format='png', engine='kaleido')
        files = {'file': ('chart.png', chart_image)}
        response = requests.post(webhook_url, files=files)
        if response.status_code == 204:
            return 'Chart sent to Discord successfully', 200
        else:
            return f'Failed to send chart to Discord: {response.status_code}', response.status_code
    else:
        return 'Failed to fetch chart data', 500

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
