import time
import requests
import re
from bs4 import BeautifulSoup

BOT_TOKEN = "8887386327:AAEArJPxnYVpYIQjMMJlt--JWkRu3u1unVQ"
CHANNEL_ID = "@krddollar"

def convert_digits(text):
    kurdish_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    return text.translate(str.maketrans(kurdish_digits, english_digits))

def get_live_rate():
    try:
        url = f"https://t.me/s/bazari_dolaraka?t={int(time.time())}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message_text")
            for msg in reversed(messages):
                raw_text = convert_digits(msg.get_text())
                matches = re.findall(r'(\d{2,3}[,.]?\d{3})', raw_text)
                for m in matches:
                    clean = int(m.replace(",", "").replace(".", ""))
                    if 140000 <= clean <= 190000:
                        return clean
    except Exception as e:
        print(f"Error: {e}", flush=True)
    return None

def send_dollar_update(price):
    try:
        message = (
            "💵 **نرخی دۆلار لە بازاڕی هەولێر**\n\n"
            f"🔹 **100 دۆلار = {price:,} دینار**\n\n"
            "📍 @krddollar"
        )
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, data=payload, timeout=10)
        print(f"پۆست کرا: {price} | وەڵامی تێلیگرام: {r.status_code}", flush=True)
    except Exception as e:
        print(f"Error sending message: {e}", flush=True)

if __name__ == "__main__":
    print("بۆتەکە دەستی پێکرد...", flush=True)
    price = get_live_rate()
    if price:
        print(f"نرخ دۆزرایەوە: {price}", flush=True)
        send_dollar_update(price)
    else:
        print("هیچ نرخێک نەدۆزرایەوە!", flush=True)
