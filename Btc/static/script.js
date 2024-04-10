let reminderIntervalId = null;
let countdownIntervalId = null;
let countdownSeconds = 0;

function updateCountdownDisplay() {
    const countdownElement = document.getElementById('countdown');
    if (countdownSeconds > 0) {
        countdownElement.textContent = countdownSeconds + ' 秒';
    } else if (loopCount === -1) {
        // 如果是无限循环，即使倒计时结束也不显示"未设置提醒"
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
            if (loopCount === -1) {
                // 如果设置为无限循环，则重置倒计时秒数并继续
                countdownSeconds = seconds;
            } else if (loopCount > 0) {
                // 如果有指定循环次数，减少一次循环计数并重置倒计时秒数
                loopCount--;
                countdownSeconds = seconds;
                if (loopCount === 0) {
                    // 如果完成了所有循环，清理倒计时器并更新显示为“未设置提醒”
                    clearInterval(countdownIntervalId);
                    countdownIntervalId = null;
                    updateCountdownDisplay();
                    return; // 退出函数
                }
            } else {
                // 如果不需要循环，清理倒计时器并更新显示为“未设置提醒”
                clearInterval(countdownIntervalId);
                countdownIntervalId = null;
                updateCountdownDisplay();
                return; // 退出函数
            }
            fetchBitcoinPrice(); // 在每次倒计时结束时获取并播报新价格
        }
    }, 1000);
}



let loopCount = 0; // 新增一个变量来存储循环次数

function openSettings() {
    let interval = prompt("请输入提醒间隔时间（秒）:", "60");
    let isLoop = document.getElementById('loopCheckbox').checked; // 获取复选框的选中状态

    if (interval !== null) {
        interval = parseInt(interval, 10);
        if (isNaN(interval) || interval <= 0) {
            alert("请输入有效的秒数");
            return;
        }
        if (isLoop) {
            loopCount = -1; // 设置为-1表示无限循环
        } else {
            loopCount = 1; // 不勾选表示不循环，仅执行一次
        }
        startCountdown(interval); // 开始倒计时，倒计时结束后将会触发价格更新
        if (reminderIntervalId !== null) {
            clearInterval(reminderIntervalId); // 清除之前的定时器（如果有）
        }
        // 设置新的提醒定时器，到时间后更新价格
        reminderIntervalId = setInterval(() => {
            if (loopCount !== 0) {
                fetchBitcoinPrice(); // 到时间后获取并播报新的比特币价格
                if (loopCount > 0) {
                    loopCount--; // 如果设置了循环次数，每次循环后减少计数
                }
            }
            if (loopCount === 0) {
                clearInterval(reminderIntervalId); // 如果循环结束，清除定时器
                reminderIntervalId = null;
            }
        }, interval * 1000);
    }
}



function stopReminder() {
    // 清除提醒定时器
    if (reminderIntervalId !== null) {
        clearInterval(reminderIntervalId);
        reminderIntervalId = null;
    }
    // 清除倒计时定时器
    if (countdownIntervalId !== null) {
        clearInterval(countdownIntervalId);
        countdownIntervalId = null;
    }
    countdownSeconds = 0; // 重置倒计时秒数
    loopCount = 0; // 重置循环计数器
    updateCountdownDisplay(); // 更新显示为“未设置提醒”
}


function fetchBitcoinPrice() {
    fetch('/get_bitcoin_price')
        .then(response => response.text())
        .then(price => {
            document.getElementById('btcPrice').textContent = price + " USD";
            speakPrice(price);
            // 如果你也更新报价时间
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
    msg.text = "当前比特币价格：" + price;
    msg.lang = "zh-CN";
    window.speechSynthesis.speak(msg);
}



// 确保fetchBitcoinPrice，speakPrice和displayQuoteTime函数定义保持不变
