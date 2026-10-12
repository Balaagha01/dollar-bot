import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# ==================== ڕێکخستنەکان ====================
BOT_TOKEN = "8887386327:AAHRlklAMGcR8D7MRngaIyYr_99UhlW2dwA"
CHANNEL_ID = "@krddollar"
SOURCE_CHANNELS = ["bazari_dolaraka", "dolar_hawler", "hawler_dolar"]

# ==================== وەرگرتنی پەیامەکان ====================
def get_channel_messages(channel_username, limit=10):
    url = f"https://t.me/s/{channel_username.replace('@', '')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            msgs = soup.find_all("div", class_="tgme_widget_message_text")
            return [m.get_text(separator="\n").strip() for m in msgs[-limit:]]
    except Exception as e:
        print(f"هەڵە لە {channel_username}: {e}", flush=True)
    return []

def extract_usd(text):
    matches = re.findall(r'(\d{2,3}[,.]?\d{3})', text)
    for m in matches:
        clean = int(m.replace(",", "").replace(".", ""))
        if 140000 <= clean <= 190000:
            return clean
    return None

def extract_gold(text):
    lines = text.split("\n")
    for line in lines:
        if any(w in line for w in ["زێڕ", "مسقاڵ", "عەیار 21", "عیار 21"]):
            matches = re.findall(r'(\d{2,3}[,.]?\d{3})', line)
            for m in matches:
                clean = int(m.replace(",", "").replace(".", ""))
                if 400000 <= clean <= 1200000:
                    return f"{clean:,}"
    return None

def extract_silver(text):
    lines = text.split("\n")
    for line in lines:
        if "زیو" in line:
            matches = re.findall(r'(\d{1,3}[,.]?\d{3})', line)
            for m in matches:
                clean = int(m.replace(",", "").replace(".", ""))
                if 4000 <= clean <= 60000:
                    return f"{clean:,}"
    return None

def fetch_all_prices():
    latest_usd = None
    latest_gold = None
    latest_silver = None

    for channel in SOURCE_CHANNELS:
        messages = get_channel_messages(channel, limit=8)
        for msg in reversed(messages):
            if not latest_usd:
                latest_usd = extract_usd(msg)
            if not latest_gold:
                latest_gold = extract_gold(msg)
            if not latest_silver:
                latest_silver = extract_silver(msg)
            if latest_usd and latest_gold and latest_silver:
                break
        if latest_usd:
            break

    return latest_usd, latest_gold, latest_silver

# ==================== ناردنی پۆست ====================
def send_telegram_photo(caption, image_filename):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    if os.path.exists(image_filename):
        with open(image_filename, "rb") as img:
            files = {"photo": img}
            data = {"chat_id": CHANNEL_ID, "caption": caption}
            requests.post(url, files=files, data=data, timeout=20)
    else:
        msg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(msg_url, json={"chat_id": CHANNEL_ID, "text": caption}, timeout=20)

def send_dollar_update(usd, last_usd, gold, silver):
    if last_usd:
        diff = usd - last_usd
        if diff > 0:
            trend_text = f"📈 بەرزبوونەوە (+{diff:,} دینار)"
            default_img = "up.jpg"
        elif diff < 0:
            trend_text = f"📉 دابەزین ({diff:,} دینار)"
            default_img = "down.jpg"
        else:
            trend_text = "🔹 جێگیر"
            default_img = "up.jpg"
    else:
        trend_text = "🔹 جێگیر"
        default_img = "up.jpg"

    caption = "💵 نرخی بازاڕ لە هەولێر\n\n"
    caption += f"🔹 100 دۆلار = {usd:,} دینار\n"
    caption += f"{trend_text}\n"

    if gold or silver:
        caption += "\n"
        if gold:
            caption += f"🥇 مسقاڵێک زێڕ (ع٢١) = {gold} دینار\n"
        if silver:
            caption += f"🥈 مسقاڵێک زیو = {silver} دینار\n"

    caption += f"\n📍 {CHANNEL_ID}"

    chosen_img = "all.jpg" if (gold or silver) else default_img
    send_telegram_photo(caption, chosen_img)
    print(f"پۆست کرا: {chosen_img}", flush=True)

# ==================== کارکردن ====================
if __name__ == "__main__":
    usd_price, gold_price, silver_price = fetch_all_prices()
    my_msgs = get_channel_messages(CHANNEL_ID)

    last_usd = None
    for msg in reversed(my_msgs):
        matches = re.findall(r'(\d{2,3}[,.]?\d{3})', msg)
        for m in matches:
            clean = int(m.replace(",", "").replace(".", ""))
            if 140000 <= clean <= 190000:
                last_usd = clean
                break
        if last_usd:
            break

    if usd_price:
        send_dollar_update(usd_price, last_usd, gold_price, silver_price)
    else:
        print("هیچ نرخێک نەدۆزرایەوە.", flush=True)
