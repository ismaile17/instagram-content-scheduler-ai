import os
import requests
import json
from datetime import datetime

APP_ID = ""
APP_SECRET = ""

def load_current_token():
    if not os.path.exists("api_keys.py"):
        return None
    with open("api_keys.py", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("INSTAGRAM_ACCESS_TOKEN"):
                return line.split("=", 1)[1].strip().strip('"')
    return None

def should_refresh_token(current_token, days_threshold=5):
    debug_url = "https://graph.facebook.com/debug_token"
    params = {
        "input_token": current_token,
        "access_token": f"{APP_ID}|{APP_SECRET}"
    }
    res = requests.get(debug_url, params=params)
    data = res.json()

    if "data" in data and "expires_at" in data["data"]:
        expires_ts = data["data"]["expires_at"]
        expires_date = datetime.fromtimestamp(expires_ts)
        days_left = (expires_date - datetime.now()).days
        print(f"🔍 Token expires in {days_left} days.")
        return days_left < days_threshold
    else:
        print("⚠️ Token süresi sorgulanamadı:", data)
        return False

def get_long_lived_token(current_token):
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": current_token
    }
    res = requests.get(url, params=params)
    data = res.json()
    if "access_token" in data:
        return data["access_token"]
    else:
        print("❌ Token yenileme başarısız:", data)
        return None

def update_api_keys(new_token):
    if not os.path.exists("api_keys.py"):
        print("❌ api_keys.py bulunamadı.")
        return
    with open("api_keys.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open("api_keys.py", "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("INSTAGRAM_ACCESS_TOKEN ="):
                f.write(f'INSTAGRAM_ACCESS_TOKEN = "{new_token}"\n')
            else:
                f.write(line)

# Ana akış
current_token = load_current_token()
if current_token:
    if should_refresh_token(current_token):
        new_token = get_long_lived_token(current_token)
        if new_token:
            update_api_keys(new_token)
            print("🔄 Token başarıyla yenilendi.")
        else:
            print("⚠️ Token yenilenemedi.")
    else:
        print("✅ Token hâlâ geçerli, yenilemeye gerek yok.")
else:
    print("❌ Mevcut token alınamadı.")
