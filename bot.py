import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# ==================== ڕێکخستنە سەرەکییەکان ====================
# تۆکنە نوێیەکەی BotFather لێرە دابنێ:
BOT_TOKEN = "8887386327:AAHRlklAMGcR8D7MRngaIyYr_99UhlW2dwA"

# کەناڵەکەت:
CHANNEL_ID = "@krddollar"

# کەناڵە سەرچاوەکان:
SOURCE_CHANNELS = ["bazari_dolaraka", "dolar_hawler", "hawler_dolar"]

# ==================== فەنکشنەکانی دەرهێنانی نرخ ====================

def get_channel_messages(channel_username, limit=10):
    """وەرگرتنی دوایین پۆستەکانی کەناڵێک لە وێبەوە"""
    url = f"https://t.me/s/{channel_username.replace('@', '')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            msgs = soup.find_all("div", class_="tgme_widget_message_text")
            return [m.get_text(separator="\n").strip() for m in msgs[-limit:]]
    except Exception as e:
        print(f"هەڵە لە سەرچاوەی {channel_username}: {e}", flush=True)
    return []

def extract_usd(text):
    """دەرهێنانی نرخی 100 دۆلار"""
    matches = re.findall(r'(\d{2,3}[,.]?\d{3})', text)
    for m in matches:
        clean = int(m.replace(",", "").replace(".", ""))
        if 140000 <= clean <= 175000:
            return clean
    return None

def extract_gold(text):
    """دەرهێنانی نرخی مسقاڵی زێڕ"""
    lines = text.split("\n")
    for line in lines:
        if any(w in line for w in ["زێڕ", "مسقاڵ", "عەیار 21", "عیار 21"]):
            matches = re.findall(r'(\d{2,3}[,.]?\d{3})', line)
            for m in matches:
                clean = int(m.replace(",", "").replace(".", ""))
                if 400000 <= clean <= 850000:
                    return f"{clean:,}"
    return None

def extract_silver(text):
    """دەرهێنانی نرخی زیو"""
    lines = text.split("\n")
    for line in lines:
        if "زیو" in line:
            matches = re.findall(r'(\d{1,3}[,.]?\d{3})', line)
            for m in matches:
                clean = int(m.replace(",", "").replace(".", ""))
                if 5000 <= clean <= 60000:
                    return f"{clean:,}"
    return None

def fetch_all_prices():
    """گەڕان لە سەرچاوەکان بەدوای دۆلار، زێڕ، زیو"""
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

# ==================== ناردنی وێنە و پۆست ====================

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
    # ژماردنی بەرزبوونەوە یان دابەزین
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

    # داڕشتنی دەق بەبێ بەروار و کاتژمێر
    caption = "💵 نرخی بازاڕ لە هەولێر\n\n"
    caption += f"🔹 100 دۆلار = {usd:,} دینار\n"
    caption += f"{trend_text}\n"

    # زیادکردنی زێڕ و زیو ئەگەر هەبن
    if gold or silver:
        caption += "\n"
        if gold:
            caption += f"🥇 مسقاڵێک زێڕ (ع٢١) = {gold} دینار\n"
        if silver:
            caption += f"🥈 مسقاڵێک زیو = {silver} دینار\n"

    caption += f"\n📍 {CHANNEL_ID}"

    # ئەگەر زێڕ یان زیو هەبێت بە all.jpg پۆست دەکات
    chosen_img = "all.jpg" if (gold or silver) else default_img

    send_telegram_photo(caption, chosen_img)
    print(f"پۆست کرا: {chosen_img}", flush=True)

# ==================== کارکردنی سەرەکی ====================

if __name__ == "__main__":
    usd_price, gold_price, silver_price = fetch_all_prices()
    
    # دۆزینەوەی کۆتا نرخی کەناڵەکەت بۆ بەراوردکردن
    my_msgs = get_channel_messages(CHANNEL_ID)
    last_usd = None
    for msg in reversed(my_msgs):
        found = extract_usd(msg)
        if found:
            last_usd = found
            break

    if usd_price:
        send_dollar_update(usd_price, last_usd, gold_price, silver_price)
    else:
        print("هیچ نرخێک نەدۆزرایەوە لە سەرچاوەکان.", flush=True)
