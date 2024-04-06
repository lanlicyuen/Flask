from flask import Flask, render_template
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

def get_current_block_height():
    # 示例API，实际使用时需要替换为可用的比特币区块链信息API
    api_url = "https://blockchain.info/q/getblockcount"
    response = requests.get(api_url)
    return int(response.text)

def calculate_days_until_halving(current_height, halving_block=840000):
    blocks_until_halving = halving_block - current_height
    # 每10分钟一个区块，一天大约有144个区块
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
    return render_template('index.html', current_date=current_date, current_height=current_height, days_until_halving=int(days_until_halving), halving_date=halving_date)

if __name__ == "__main__":
    app.run(debug=True, port=81)