import os
import json
import requests
import urllib.parse

BOT_TOKEN = "8887386327:AAEArJPxnYVpYIQjMMJlt--JWkRu3u1unVQ"
CHANNEL_ID = "@krddollar"

caption = (
    "💵 **نرخی بازاڕ لە هەولێر**\n\n"
    "🔹 **100 دۆلار = 153,250 دینار**\n"
    "👑 **1 مسقاڵ زێڕ (عەیار 21): 585,000 دینار**\n"
    "⚪️ **1 مسقاڵ زیو: 22,000 دینار**\n\n"
    "📍 @krddollar"
)

share_msg = urllib.parse.quote("📊 نوێترین نرخەکانی بازاڕی هەولێر")
buttons = {
    "inline_keyboard": [
        [
            {"text": "📢 جۆینکردن", "url": "https://t.me/krddollar"},
            {"text": "🔄 ناردن", "url": f"https://t.me/share/url?url=https://t.me/krddollar&text={share_msg}"}
        ]
    ]
}

# پشکنینی بوونی وێنەکە
if os.path.exists("all.jpg"):
    print("وێنەی all.jpg دۆزرایەوە، پۆستەکە دەنێردرێت...")
    with open("all.jpg", "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "Markdown", "reply_markup": json.dumps(buttons)},
            files={"photo": f}
        )
else:
    print("⚠️ وێنەی all.jpg نەدۆزرایەوە! پۆستەکە بە تێکست تاقی دەکرێتەوە...")
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHANNEL_ID, "text": caption, "parse_mode": "Markdown", "reply_markup": json.dumps(buttons)}
    )

print("ئەنجامی تێلیگرام:", r.status_code, r.text)
