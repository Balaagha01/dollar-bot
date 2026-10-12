import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# ==================== ڕێکخستنە سەرەکییەکان ====================
# تۆکنە نوێیەکەی کە لە BotFather وەرتگرت لێرە لە نێوان جووت کەوانەکەدا دابنێ:
BOT_TOKEN = "8887386327:AAHRlklAMGcR8D7MRngaIyYr_99UhlW2dwA"

# ئایدی کەناڵەکەت:
CHANNEL_ID = "@krddollar"

# ئەو کەناڵانەی نرخەکانیان لێ وەردەگیرێت:
SOURCE_CHANNELS = ["bazari_dolaraka", "dolar_hawler", "hawler_dolar"]

# ==================== فەنکشنەکانی دەرهێنانی نرخ ====================

def get_channel_messages(channel_username, limit=10):
    """وەرگرتنی دوایین نامەکانی کەناڵێک لە ڕێگەی تێلیگرام وێبەوە"""
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
        print(f"هەڵە لە خوێندنەوەی کەناڵی {channel_username}: {e}", flush=True)
    return []

def extract_usd(text):
    """دۆزینەوەی نرخی 100 دۆلار"""
    # گەڕان بەدوای ژمارەی نێوان 140,000 تا 170,000
    matches = re.findall(r'(\d{2,3}[,.]?\d{3})', text)
    for m in matches:
        clean = int(m.replace(",", "").replace(".", ""))
        if 140000 <= clean <= 170000:
            return clean
    return None

def extract_gold(text):
    """دۆزینەوەی نرخی مسقاڵی زێڕ (عەیار 21 یان نرخی گشتی)"""
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
    """دۆزینەوەی نرخی زیو"""
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
    """پشکنینی هەرسێ سەرچاوەکە بۆ دۆزینەوەی دۆلار، زێڕ و زیو"""
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

# ==================== ناردنی پۆست بۆ تێلیگرام ====================

def send_telegram_photo(caption, image_filename):
    """ناردنی وێنە لەگەڵ دەق بۆ کەناڵەکەت"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    if os.path.exists(image_filename):
        with open(image_filename, "rb") as img:
            files = {"photo": img}
            data = {"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"}
            requests.post(url, files=files, data=data, timeout=20)
    else:
        # ئەگەر وێنەکە بەردەست نەبوو، وەک دەقی ئاسایی بینێرێت تا کارەکە نەوەستێت
        msg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(msg_url, json={"chat_id": CHANNEL_ID, "text": caption, "parse_mode": "HTML"}, timeout=20)

def send_dollar_update(usd, last_usd, gold, silver):
    """ڕێکخستنی دەقی پۆستەکە و هەڵبژاردنی وێنەی گونجاو"""
    kurd_time = datetime.now(timezone(timedelta(hours=3)))
    time_str = kurd_time.strftime("%I:%M %p")
    date_str = kurd_time.strftime("%Y/%m/%d")

    # دیاریکردنی ئاراستەی نرخ
    if last_usd and usd > last_usd:
        trend_text = "🔺 بەرزبوونەوە"
        default_img = "up.jpg"
    elif last_usd and usd < last_usd:
        trend_text = "🔻 دابەزین"
        default_img = "down.jpg"
    else:
        trend_text = "🔹 جێگیر"
        default_img = "up.jpg"

    # دەقی پەیامەکە
    caption = f"📊 <b>نرخی بازاڕی هەولێر</b>\n\n"
    caption += f"💵 <b>$100 دۆلار:</b> {usd:,} دینار ({trend_text})\n"

    if gold:
        caption += f"🥇 <b>مسقاڵێک زێڕ (ع٢١):</b> {gold} دینار\n"
    if silver:
        caption += f"🥈 <b>مسقاڵێک زیو:</b> {silver} دینار\n"

    caption += f"\n⏰ کاتژمێر: {time_str}\n"
    caption += f"📅 بەروار: {date_str}\n\n"
    caption += f"🆔 {CHANNEL_ID}"

    # ئەگەر زێڕ یان زیو بەردەست بێت، وێنەی all.jpg بەکاردەهێنرێت
    chosen_img = "all.jpg" if (gold or silver) else default_img

    send_telegram_photo(caption, chosen_img)
    print(f"پۆست کرا: USD={usd}, Gold={gold}, Silver={silver} بە وێنەی {chosen_img}", flush=True)

def handle_daily_market_close(my_msgs, current_usd, today_str, gold, silver):
    """پۆستکردنی داخرانی بازاڕ لە دەوروبەری کاتژمێر 7ی ئێوارە"""
    caption = f"🔒 <b>داخرانی بازاڕی هەولێر</b>\n\n"
    caption += f"💵 <b>کۆتا نرخی $100 دۆلار:</b> {current_usd:,} دینار\n"
    if gold:
        caption += f"🥇 <b>مسقاڵی زێڕ:</b> {gold} دینار\n"
    if silver:
        caption += f"🥈 <b>مسقاڵی زیو:</b> {silver} دینار\n"

    caption += f"\n📅 بەروار: {today_str}\n\n"
    caption += f"🆔 {CHANNEL_ID}"

    send_telegram_photo(caption, "close.jpg")
    print("داخرانی بازاڕ پۆست کرا.", flush=True)

# ==================== جێبەجێکردنی سەرەکی ====================

if __name__ == "__main__":
    kurd_time = datetime.now(timezone(timedelta(hours=3)))
    current_hour = kurd_time.hour
    current_minute = kurd_time.minute
    today_str = kurd_time.strftime("%Y/%m/%d")

    # وەرگرتنی نرخەکان لە کەناڵە سەرچاوەکان
    usd_price, gold_price, silver_price = fetch_all_prices()
    
    # وەرگرتنی دوایین نرخی ناو کەناڵەکەی خۆت
    my_msgs = get_channel_messages(CHANNEL_ID)
    last_usd = None
    for msg in reversed(my_msgs):
        found = extract_usd(msg)
        if found:
            last_usd = found
            break

    # ئەگەر نرخی دۆلار دۆزرایەوە، دەستبەجێ پۆست دەکات
    if usd_price:
        is_closing_time = (current_hour == 18 and current_minute >= 50) or (current_hour == 19 and current_minute <= 20)

        if is_closing_time:
            handle_daily_market_close(my_msgs, usd_price, today_str, gold_price, silver_price)
        else:
            send_dollar_update(usd_price, last_usd, gold_price, silver_price)
    else:
        print("هیچ نرخێکی نوێ نەدۆزرایەوە لە سەرچاوەکان.", flush=True)
