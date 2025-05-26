import requests
import os
import time
import hmac
import hashlib
import json
from datetime import datetime

# KONFIGURATION (aus Render Environment lesen)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SYMBOL = "DOGEUSDT"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Telegram-Nachricht senden
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Telegram Fehler:", e)

# Signatur für Bybit REST
def create_signature(params: dict, secret: str):
    sorted_params = sorted(params.items())
    query = '&'.join(f"{k}={v}" for k, v in sorted_params)
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()

# Beispiel-Funktion zur Prüfung von Wallet (später erweiterbar)
def check_wallet():
    try:
        timestamp = int(time.time() * 1000)
        params = {
            "api_key": API_KEY,
            "timestamp": timestamp
        }
        sign = create_signature(params, API_SECRET)
        params["sign"] = sign
        response = requests.get("https://api.bybit.com/v2/private/wallet/balance", params=params)
        data = response.json()
        if "result" in data and "DOGE" in data["result"]:
            balance = data["result"]["DOGE"]["available_balance"]
            return float(balance)
        return 0.0
    except Exception as e:
        print("Fehler beim Wallet Abruf:", e)
        return 0.0

# Hauptfunktion
def run_bot():
    send_telegram_message("✅ GridBot wurde erfolgreich gestartet.")
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot läuft...")
        balance = check_wallet()
        send_telegram_message(f"📊 Aktuelles DOGE Guthaben: {balance} DOGE")
        time.sleep(900)  # 15 Minuten warten

# Einstiegspunkt
if __name__ == "__main__":
    run_bot()
