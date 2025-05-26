
import requests
import time
import hmac
import hashlib
import json
from datetime import datetime
import os

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SYMBOL = "DOGEUSDT"
BASE_URL = "https://api.bybit.com"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 15 * 60

def get_timestamp():
    return int(time.time() * 1000)

def create_signature(secret, params: dict) -> str:
    sorted_params = dict(sorted(params.items()))
    query_string = '&'.join(f"{k}={v}" for k, v in sorted_params.items())
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Fehler:", e)

def get_wallet_balance():
    url = f"{BASE_URL}/v5/account/wallet-balance"
    timestamp = str(get_timestamp())
    params = {
        "accountType": "UNIFIED",
        "coin": "DOGE",
        "timestamp": timestamp
    }
    sign = create_signature(API_SECRET, params)
    headers = {
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": sign
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        doge = float(data["result"]["list"][0]["coin"][0]["availableToTrade"])
        send_telegram_message(f"📊 DOGE Guthaben: {doge}")
        return doge
    except Exception as e:
        send_telegram_message(f"Wallet Fehler: {e}")
        return 0.0

def place_order(side, price, qty):
    url = f"{BASE_URL}/v5/order/create"
    timestamp = str(get_timestamp())
    body = {
        "category": "spot",
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC",
        "timestamp": timestamp
    }
    sign = create_signature(API_SECRET, body)
    headers = {
        "Content-Type": "application/json",
        "X-BAPI-API-KEY": API_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": sign
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        send_telegram_message(f"📨 {side} ➜ {qty} @ {price} USDT — Order gesendet.
Antwort: {response.text}")
    except Exception as e:
        send_telegram_message(f"❌ Order Fehler: {e}")

def run_bot():
    send_telegram_message("✅ GridBot ist aktiv.")
    while True:
        now = datetime.now().strftime('%H:%M:%S')
        send_telegram_message(f"⏱ GridBot läuft (15 Min). {SYMBOL} Grid aktiv [{now}]")

        place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
        time.sleep(5)
        balance = get_wallet_balance()

        if balance >= GRID_QTY:
            place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
        else:
            send_telegram_message("⚠️ Noch nicht genug DOGE für Verkauf.")

        send_telegram_message("⏱ Nächste Prüfung in 15 Minuten.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()
