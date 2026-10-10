import time
import requests
import re
import os
import json
import urllib.parse
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN", "8887386327:AAEArJPxnYVpYIQjMMJlt--JWkRu3u1unVQ")
CHANNEL_ID = "@krddollar"

SOURCE_CHANNELS = ["bazari_dolaraka", "dolar_hawler", "hawler_dolar"]

IMAGE_UP = "up.jpg"
IMAGE_DOWN = "down.jpg"
IMAGE_CLOSE = "close.jpg"

FLASH_ALERT_LIMIT = 1000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

def convert_digits(text):
    kurdish_digits = "٠١٢٣٤٥٦٧٨٩"
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(kurdish_digits, english_digits))
    return text.translate(str.maketrans(persian_digits, english_digits))

def get_channel_messages(channel_username):
    try:
        clean_user = channel_username.replace("@", "")
        url = f"https://t.me/s/{clean_user}?t={int(time.time())}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            return [convert_digits(m.get_text()) for m in soup.find_all("div", class_="tgme_widget_message_text")]
    except Exception as e:
        print(f"هەڵە لە کەناڵی {channel_username}: {e}", flush=True)
    return []

def extract_market_rates(messages):
    usd_price = None
    gold_21_price = None
    silver_price = None

    # تەنها لە ١٢ پەیامی کۆتایی بگەڕێ تا نرخی ڕۆژانی پێشوو نەهێنێت
    recent_messages = list(reversed(messages))[:12]

    for msg in recent_messages:
        # ١. دەرهێنانی نرخی دۆلار
        if not usd_price:
            matches = re.findall(r'(\d{2,3}[,.]?\d{3})', msg)
            for m in matches:
                clean = int(m.replace(",", "").replace(".", ""))
                if 140000 <= clean <= 190000:
                    usd_price = clean
                    break

        # ٢. دەرهێنانی نرخی زێڕی عەیار ٢١
        if not gold_21_price:
            g_match = re.search(r'(?:عیار|عەیار|عەیاری|عیاری|زێڕ|زێر)\s*21[^\d]*(\d{2,3}[,.]?\d{3})', msg)
            if g_match:
                clean_g = int(g_match.group(1).replace(",", "").replace(".", ""))
                if 400000 <= clean_g <= 850000:
                    gold_21_price = clean_g
            else:
                g_hazar = re.search(r'(?:عیار|عەیار|عەیاری|عیاری|زێڕ|زێر)\s*21[^\d]*(\d{3})\s*هەزار', msg)
                if g_hazar:
                    clean_g = int(g_hazar.group(1)) * 1000
                    if 400000 <= clean_g <= 850000:
                        gold_21_price = clean_g

        # ٣. دەرهێنانی نرخی زێو
        if not silver_price:
            s_match = re.search(r'(?:زێو|زیو)[^\d]*(\d{1,2}[,.]?\d{3})', msg)
            if s_match:
                clean_s = int(s_match.group(1).replace(",", "").replace(".", ""))
                if 4000 <= clean_s <= 50000:
                    silver_price = clean_s
            else:
                s_hazar = re.search(r'(?:زێو|زیو)[^\d]*(\d{1,2})\s*هەزار', msg)
                if s_hazar:
                    clean_s = int(s_hazar.group(1)) * 1000
                    if 4000 <= clean_s <= 50000:
                        silver_price = clean_s

    return usd_price, gold_21_price, silver_price

def fetch_all_prices():
    best_usd = None
    best_gold = None
    best_silver = None

    for ch in SOURCE_CHANNELS:
        msgs = get_channel_messages(ch)
        u, g, s = extract_market_rates(msgs)
        if not best_usd and u:
            best_usd = u
        if not best_gold and g:
            best_gold = g
        if not best_silver and s:
            best_silver = s

    print(f"ئەنجامی پشکنین: دۆلار={best_usd}, زێڕ={best_gold}, زێو={best_silver}", flush=True)
    return best_usd, best_gold, best_silver

def add_reaction(message_id, emoji):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
        payload = {
            "chat_id": CHANNEL_ID,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}]
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"هەڵە لە کاردانەوە: {e}", flush=True)

def send_dollar_update(new_price, old_price=None, gold_price=None, silver_price=None):
    try:
        status_line = ""
        alert_badge = ""
        selected_image = IMAGE_UP
        reaction_emoji = "👍"

        if old_price:
            diff = abs(new_price - old_price)
            if diff >= FLASH_ALERT_LIMIT:
                alert_badge = "\n🚨 **ئاگاداری: جووڵەی بەهێزی بازاڕ!**"

            if new_price > old_price:
                status_line = f"\n📈 **بەرزبوونەوە (+{diff:,} دینار)**"
                selected_image = IMAGE_UP
                reaction_emoji = "👍"
            elif new_price < old_price:
                status_line = f"\n📉 **دابەزین (-{diff:,} دینار)**"
                selected_image = IMAGE_DOWN
                reaction_emoji = "👎"

        extra_rates = ""
        if gold_price:
            extra_rates += f"\n👑 **1 مسقاڵ زێڕ (عەیار 21): {gold_price:,} دینار**"
        if silver_price:
            extra_rates += f"\n⚪️ **1 مسقاڵ زێو: {silver_price:,} دینار**"

        caption = (
            "💵 **نرخی بازاڕ لە هەولێر**\n\n"
            f"🔹 **100 دۆلار = {new_price:,} دینار**{status_line}{extra_rates}{alert_badge}\n\n"
            "📍 @krddollar"
        )

        share_msg = urllib.parse.quote("📊 نوێترین نرخی دۆلار و زێڕ لە بازاڕی هەولێر 💵")
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "📢 جۆینکردن", "url": "https://t.me/krddollar"},
                    {"text": "🔄 ناردن", "url": f"https://t.me/share/url?url=https://t.me/krddollar&text={share_msg}"}
                ]
            ]
        }

        if os.path.exists(selected_image):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(selected_image, "rb") as f:
                r = requests.post(url, data={"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "Markdown", "reply_markup": json.dumps(buttons)}, files={"photo": f}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": caption, "parse_mode": "Markdown", "reply_markup": json.dumps(buttons)}, timeout=10)

        if r and r.status_code == 200:
            msg_id = r.json().get("result", {}).get("message_id")
            if msg_id:
                add_reaction(msg_id, reaction_emoji)
        print("پۆستی ئاسایی نێردرا.", flush=True)
    except Exception as e:
        print(f"هەڵە لە پۆست: {e}", flush=True)

def handle_daily_market_close(my_channel_messages, current_price, today_date_str, gold_price=None, silver_price=None):
    try:
        # ئەگەر بەرواری ئەمڕۆ لە پۆستەکانی داخراندا هەبێت، دووبارەی ناکاتەوە
        for msg in my_channel_messages[-8:]:
            if "داخرانی بازاڕ" in msg and today_date_str in msg:
                print("پۆستی داخران پێشتر بۆ ئەمڕۆ کراوە.", flush=True)
                return

        usd_prices = []
        for msg in my_channel_messages:
            matches = re.findall(r'(\d{2,3}[,.]?\d{3})', msg)
            for m in matches:
                clean = int(m.replace(",", "").replace(".", ""))
                if 140000 <= clean <= 190000:
                    usd_prices.append(clean)

        if not usd_prices:
            usd_prices = [current_price]
        else:
            usd_prices.append(current_price)

        high_p = max(usd_prices)
        low_p = min(usd_prices)

        close_caption = (
            f"🔒 **داخرانی بازاڕ لە هەولێر** ({today_date_str})\n\n"
            f"🔹 **دۆلار: {current_price:,} دینار**\n"
            f"🔺 **بەرزترین: {high_p:,} دینار**\n"
            f"🔻 **نزمترین: {low_p:,} دینار**"
        )
        if gold_price:
            close_caption += f"\n👑 **زێڕ (عەیار 21): {gold_price:,} دینار**"
        if silver_price:
            close_caption += f"\n⚪️ **زێو: {silver_price:,} دینار**"

        close_caption += "\n\n📍 @krddollar"

        share_msg = urllib.parse.quote("🔒 پوختەی داخرانی بازاڕ لە هەولێر 💵")
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "📢 جۆینکردن", "url": "https://t.me/krddollar"},
                    {"text": "🔄 ناردن", "url": f"https://t.me/share/url?url=https://t.me/krddollar&text={share_msg}"}
                ]
            ]
        }

        if os.path.exists(IMAGE_CLOSE):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(IMAGE_CLOSE, "rb") as f:
                r = requests.post(url, data={"chat_id": CHANNEL_ID, "caption": close_caption, "parse_mode": "Markdown", "reply_markup": json.dumps(buttons)}, files={"photo": f}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": close_caption, "parse_mode": "Markdown", "reply_markup": json.dumps(buttons)}, timeout=10)

        if r and r.status_code == 200:
            msg_id = r.json().get("result", {}).get("message_id")
            if msg_id:
                add_reaction(msg_id, "🔒")
        print("پۆستی داخران بە سەرکەوتوویی نێردرا.", flush=True)
    except Exception as e:
        print(f"هەڵە لە پۆستی داخران: {e}", flush=True)

if __name__ == "__main__":
    kurd_time = datetime.now(timezone(timedelta(hours=3)))
    current_hour = kurd_time.hour
    current_minute = kurd_time.minute
    today_str = kurd_time.strftime("%Y/%m/%d")

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
        is_closing_time = (current_hour == 18 and current_minute >= 50) or (current_hour == 19 and current_minute <= 20)

        if is_closing_time:
            handle_daily_market_close(my_msgs, usd_price, today_str, gold_price, silver_price)
        elif usd_price != last_usd:
            send_dollar_update(usd_price, last_usd, gold_price, silver_price)
