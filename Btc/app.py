from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import requests
import pytz


app = Flask(__name__)

def fetch_bitcoin_price_server():
    # 使用Binance API获取BTC对USDT的价格
    response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
    data = response.json()
    # 保留价格的小数点后两位
    price = "{:.2f}".format(float(data['price']))

    # 获取当前时间，并调整为香港时区（UTC+8）
    tz_hk = pytz.timezone('Asia/Hong_Kong')
    now_hk = datetime.now(tz_hk)
    time_str = now_hk.strftime("%Y-%m-%d %H:%M:%S")  # 格式化时间字符串

    return price, time_str  # 返回价格和时间字符串

def get_current_block_height():
    # 示例API，实际使用时需要替换为可用的比特币区块链信息API
    api_url = "https://blockchain.info/q/getblockcount"
    response = requests.get(api_url)
    return int(response.text)

def calculate_days_until_halving(current_height, halving_block=840000):
    blocks_until_halving = halving_block - current_height
    days_until_halving = blocks_until_halving / 144
    return days_until_halving

def calculate_date_of_halving(days_until_halving):
    current_date = datetime.now()
    halving_date = current_date + timedelta(days=days_until_halving)
    return halving_date.strftime("%Y-%m-%d")

@app.route('/')
def home():
    current_height = get_current_block_height()
    days_until_halving = calculate_days_until_halving(current_height)
    halving_date = calculate_date_of_halving(days_until_halving)
    current_date = datetime.now().strftime("%Y-%m-%d")
    # 获取比特币价格和时间
    bitcoin_price, price_time = fetch_bitcoin_price_server()
    # 传递比特币价格和时间到模板
    return render_template('index.html', current_date=current_date, current_height=current_height, days_until_halving=int(days_until_halving), halving_date=halving_date, bitcoin_price=bitcoin_price, price_time=price_time)


@app.route('/get_bitcoin_price')
def get_bitcoin_price():
    response = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
    data = response.json()
    price = float(data['price'])
    return jsonify({'price': price})  # 确保以JSON格式返回价格

if __name__ == "__main__":
    app.run(debug=True, port=81)
