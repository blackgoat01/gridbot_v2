import os
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# API-Zugangsdaten aus Render ENV
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Grid-Konfiguration
SYMBOL = "DOGEUSDT"
CATEGORY = "spot"
GRID_QTY = 45
GRID_BUY_PRICE = 0.2182
GRID_SELL_PRICE = 0.2204
CHECK_INTERVAL = 900  # alle 15 Minuten

# Telegram senden
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram-Fehler:", e)

# Signatur für V5
def create_signature(body: dict, secret: str):
    payload = json.dumps(body)
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

# Headers für Bybit
def get_headers():
    return {
        "X-BAPI-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

# Order platzieren
def place_order(side, price, qty):
    url = "https://api.bybit.com/v5/order/create"
    timestamp = int(time.time() * 1000)
    body = {
        "category": CATEGORY,
        "symbol": SYMBOL,
        "side": side,
        "order_type": "Limit",
        "qty": str(qty),
        "price": str(price),
        "time_in_force": "GTC",
        "timestamp": timestamp
    }
    signature = create_signature(body, API_SECRET)
    headers = get_headers()
    headers["X-BAPI-SIGN"] = signature
    headers["X-BAPI-TIMESTAMP"] = str(timestamp)

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body))
        res = response.json()
        send_telegram(f"📨 {side} Order ➜ {qty} @ {price} USDT\nAntwort: {res.get('retMsg')}")
    except Exception as e:
        send_telegram(f"❌ Fehler bei {side}-Order: {e}")

# Wallet-Abfrage
def get_wallet_balance():
    url = "https://api.bybit.com/v5/account/wallet-balance"
    timestamp = int(time.time() * 1000)
    params = {
        "accountType": "UNIFIED",
        "coin": "DOGE",
        "timestamp": timestamp
    }
    signature = create_signature(params, API_SECRET)
    headers = get_headers()
    headers["X-BAPI-SIGN"] = signature
    headers["X-BAPI-TIMESTAMP"] = str(timestamp)

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return float(data["result"]["list"][0]["coin"][0]["availableToWithdraw"])
    except Exception as e:
        print("Wallet Fehler:", e)
        return 0.0

# Haupt-Loop
def run_bot():
    send_telegram("🚀 GridBot ist aktiv.")
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot läuft...")

        # 1. Kaufsignal setzen
        place_order("Buy", GRID_BUY_PRICE, GRID_QTY)
        time.sleep(5)

        # 2. Wallet prüfen
        balance = get_wallet_balance()
        print("DOGE im Wallet:", balance)

        if balance >= GRID_QTY:
            # 3. Verkaufs-Order setzen
            place_order("Sell", GRID_SELL_PRICE, GRID_QTY)
        else:
            send_telegram("⚠️ Noch kein DOGE gekauft – Verkauf übersprungen.")

        # 4. Warten
        send_telegram(f"⏱ Nächste Prüfung in {CHECK_INTERVAL // 60} Minuten.")
        time.sleep(CHECK_INTERVAL)

# Startpunkt
if __name__ == "__main__":
    run_bot()
