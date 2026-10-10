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

# سەرچاوەکانی وەرگرتنی نرخ
SOURCE_CHANNELS = ["bazari_dolaraka", "dolar_hawler", "hawler_dolar"]

# فایلەکانی وێنە
IMAGE_UP = "up.jpg"
IMAGE_DOWN = "down.jpg"
IMAGE_CLOSE = "close.jpg" # وێنەی تایبەتی داخران
FLASH_ALERT_LIMIT = 1000  # بڕی گۆڕانکاری بۆ ئاگاداری بەپەلە

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

def convert_digits(text):
    kurdish_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    return text.translate(str.maketrans(kurdish_digits, english_digits))

def get_channel_messages(channel_username):
    try:
        clean_user = channel_username.replace("@", "")
        url = f"https://t.me/s/{clean_user}?t={int(time.time())}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            return [convert_digits(m.get_text()) for m in soup.find_all("div", class_="tgme_widget_message_text")]
    except Exception as e:
        print(f"هەڵە لە وەرگرتنی کەناڵی {channel_username}: {e}", flush=True)
    return []

def extract_prices_from_texts(messages):
    prices = []
    for msg in messages:
        matches = re.findall(r'(\d{2,3}[,.]?\d{3})', msg)
        for m in matches:
            clean = int(m.replace(",", "").replace(".", ""))
            if 140000 <= clean <= 190000:
                prices.append(clean)
    return prices

def fetch_market_price():
    for ch in SOURCE_CHANNELS:
        msgs = get_channel_messages(ch)
        prices = extract_prices_from_texts(msgs)
        if prices:
            print(f"نرخ لە [{ch}] دۆزرایەوە: {prices[-1]}", flush=True)
            return prices[-1]
    return None

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
        print(f"هەڵە لە ئیمۆجی: {e}", flush=True)

def send_dollar_update(new_price, old_price=None):
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

        caption = (
            "💵 **نرخی دۆلار لە بازاڕی هەولێر**\n\n"
            f"🔹 **100 دۆلار = {new_price:,} دینار**{status_line}{alert_badge}\n\n"
            "📍 @krddollar"
        )

        share_msg = urllib.parse.quote("📊 نوێترین نرخی دۆلار لە بازاڕی هەولێر 💵")
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "📢 جۆینکردن", "url": "https://t.me/krddollar"},
                    {"text": "🔄 ناردن", "url": f"https://t.me/share/url?url=https://t.me/krddollar&text={share_msg}"}
                ]
            ]
        }

        r = None
        if os.path.exists(selected_image):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(selected_image, "rb") as f:
                payload = {
                    "chat_id": CHANNEL_ID,
                    "caption": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(buttons)
                }
                r = requests.post(url, data=payload, files={"photo": f}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": CHANNEL_ID,
                "text": caption,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(buttons)
            }
            r = requests.post(url, data=payload, timeout=10)

        if r and r.status_code == 200:
            msg_id = r.json().get("result", {}).get("message_id")
            if msg_id:
                add_reaction(msg_id, reaction_emoji)
    except Exception as e:
        print(f"کێشە لە پۆستی گۆڕانکاری: {e}", flush=True)

def handle_daily_market_close(my_channel_messages, current_price):
    """ناردنی کورتەی داخرانی ئێواران لەگەڵ وێنە"""
    try:
        # پشکنین بۆ ئەوەی ڕۆژانە تەنها یەکجار بنێردرێت
        for msg in my_channel_messages[-5:]:
            if "داخرانی بازاڕ" in msg:
                print("پۆستی داخران ئەمڕۆ پێشتر کراوە.", flush=True)
                return

        all_today_prices = extract_prices_from_texts(my_channel_messages)
        if not all_today_prices:
            all_today_prices = [current_price]
        else:
            all_today_prices.append(current_price)

        high_p = max(all_today_prices)
        low_p = min(all_today_prices)

        close_caption = (
            "🔒 **داخرانی بازاڕی دۆلار لە هەولێر**\n\n"
            f"🔹 **نرخی کۆتایی: {current_price:,} دینار**\n"
            f"🔺 **بەرزترین نرخ: {high_p:,} دینار**\n"
            f"🔻 **نزمترین نرخ: {low_p:,} دینار**\n\n"
            "📍 @krddollar"
        )

        share_msg = urllib.parse.quote("🔒 پوختەی داخرانی بازاڕی دۆلار لە هەولێر 💵")
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "📢 جۆینکردن", "url": "https://t.me/krddollar"},
                    {"text": "🔄 ناردن", "url": f"https://t.me/share/url?url=https://t.me/krddollar&text={share_msg}"}
                ]
            ]
        }

        # ناردنی وێنەی close.jpg ئەگەر هەبێت، ئەگەر نەبوو وەک دەق دەینێرێت
        if os.path.exists(IMAGE_CLOSE):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(IMAGE_CLOSE, "rb") as f:
                payload = {
                    "chat_id": CHANNEL_ID,
                    "caption": close_caption,
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(buttons)
                }
                r = requests.post(url, data=payload, files={"photo": f}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": CHANNEL_ID,
                "text": close_caption,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(buttons)
            }
            r = requests.post(url, data=payload, timeout=10)

        if r and r.status_code == 200:
            msg_id = r.json().get("result", {}).get("message_id")
            if msg_id:
                add_reaction(msg_id, "🔒") # ئیمۆجی قفڵ لە کاتی داخران
        print("پۆستی داخران بە سەرکەوتوویی کرا.", flush=True)
    except Exception as e:
        print(f"هەڵە لە پۆستی داخران: {e}", flush=True)

if __name__ == "__main__":
    print("سیستمی زیرەک دەستی پێکرد...", flush=True)
    kurd_time = datetime.now(timezone(timedelta(hours=3)))
    current_hour = kurd_time.hour
    current_minute = kurd_time.minute
    print(f"کاتی کوردستان: {kurd_time.strftime('%I:%M %p')}", flush=True)

    current_price = fetch_market_price()
    my_msgs = get_channel_messages(CHANNEL_ID)
    my_prices = extract_prices_from_texts(my_msgs)
    last_posted_price = my_prices[-1] if my_prices else None

    # ١. پشکنینی پۆستی ئاسایی
    if current_price and current_price != last_posted_price:
        send_dollar_update(current_price, last_posted_price)

    # ٢. پۆستی داخرانی ئێواران (نێوان 06:50ی ئێوارە تا 07:20)
    if (current_hour == 18 and current_minute >= 50) or (current_hour == 19 and current_minute <= 20):
        if current_price:
            handle_daily_market_close(my_msgs, current_price)

    # ٢. پشکنینی کاتی داخرانی بازاڕ (نێوان 06:50 تا 07:20ی ئێوارە)
    if (current_hour == 18 and current_minute >= 50) or (current_hour == 19 and current_minute <= 20):
        if current_price:
            handle_daily_market_close(my_msgs, current_price)
