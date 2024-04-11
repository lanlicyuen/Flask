let reminderIntervalId = null;
let countdownIntervalId = null;
let countdownSeconds = 0;
let loopCount = 0;

function updateCountdownDisplay() {
    const countdownElement = document.getElementById('countdown');
    if (countdownSeconds > 0) {
        countdownElement.textContent = countdownSeconds + ' 秒';
    } else if (loopCount === -1) {
        countdownElement.textContent = "正在循环提醒...";
    } else {
        countdownElement.textContent = '未设置提醒';
        if (countdownIntervalId !== null) {
            clearInterval(countdownIntervalId);
            countdownIntervalId = null;
        }
    }
}

function startCountdown(seconds) {
    countdownSeconds = seconds;
    updateCountdownDisplay();
    if (countdownIntervalId !== null) {
        clearInterval(countdownIntervalId);
    }
    countdownIntervalId = setInterval(() => {
        countdownSeconds--;
        updateCountdownDisplay();
        if (countdownSeconds <= 0) {
            clearInterval(countdownIntervalId);
            countdownIntervalId = null;
            updateCountdownDisplay();
            fetchBitcoinPrice();
            if (loopCount === -1) {
                startCountdown(seconds);
            }
        }
    }, 1000);
}

function openSettings() {
    clearInterval(reminderIntervalId);
    reminderIntervalId = null;
    
    let interval = prompt("请输入提醒间隔时间（秒）:", "60");
    let isLoop = document.getElementById('loopCheckbox').checked;

    if (interval !== null) {
        interval = parseInt(interval, 10);
        if (isNaN(interval) || interval <= 0) {
            alert("请输入有效的秒数");
            return;
        }
        loopCount = isLoop ? -1 : 0;
        startCountdown(interval);
    }
}

function stopReminder() {
    clearInterval(reminderIntervalId);
    reminderIntervalId = null;
    
    clearInterval(countdownIntervalId);
    countdownIntervalId = null;
    
    countdownSeconds = 0;
    loopCount = 0;
    updateCountdownDisplay();
}

function fetchBitcoinPrice() {
    fetch('/get_bitcoin_price')
        .then(response => response.json())
        .then(data => {
            let price = parseFloat(data.price);
            let intPrice = Math.floor(price); // 只取整数部分
            document.getElementById('btcPrice').textContent = intPrice + " USD";
            if (document.getElementById('voiceAnnouncementCheckbox').checked) {
                speakPrice(intPrice.toString()); // 仅当勾选了语音播报时才播报
            }
            let now = new Date();
            let timeString = now.toLocaleString("zh-CN", {timeZone: "Asia/Shanghai"});
            document.getElementById('quoteTime').textContent = "报价时间：" + timeString;
        })
        .catch(error => {
            console.error('Error fetching Bitcoin price:', error);
        });
}

function speakPrice(price) {
    var msg = new SpeechSynthesisUtterance();
    let selectedLang = document.getElementById('languageSelect').value;

    if (document.getElementById('readPriceAsNumberCheckbox').checked) {
        // 如果勾选了“仅以数字形式读出价格”，则仅读出数字的每一位
        let priceAsText = price.split('').join(' ');
        msg.text = priceAsText; // 直接读出数字的每一位
    } else {
        // 根据选择的语言设置不同的msg.text
        switch(selectedLang) {
            case 'en-US':
                msg.text = "The Bitcoin price is: " + price + " dollars";
                break;
            case 'zh-CN':
                msg.text = "当前比特币价格：" + price + "美元";
                break;
            case 'zh-HK':
                msg.text = "現時比特幣價格：" + price + "美金";
                break;
            case 'ja-JP':
                msg.text = "現在のビットコインの価格は：" + price + "ドルです";
                break;
            default:
                msg.text = "当前比特币价格：" + price + "美元";
        }
    }

    msg.lang = selectedLang; // 设置语音播报的语言
    window.speechSynthesis.speak(msg);
}
