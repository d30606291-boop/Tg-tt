#!/usr/bin/env python3
import os, asyncio, tempfile, logging, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import yt_dlp
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)

API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION  = "userbot"

client = TelegramClient(SESSION, API_ID, API_HASH)

SUPPORTED = (
    "tiktok.com","youtube.com","youtu.be","vk.com","vkvideo.ru",
    "instagram.com","twitter.com","x.com","reddit.com","kick.com",
    "twitch.tv","vimeo.com","dailymotion.com","facebook.com","fb.watch","rumble.com",
)

YDL_OPTS = {
    "format": "bv*+ba/b",
    "merge_output_format": "mp4",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "retries": 10,
    "fragment_retries": 10,
}


class Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, *a): pass


def start_ping_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Ping).serve_forever()


@client.on(events.NewMessage(pattern=r"^\.tt\s+(https?://\S+)", outgoing=True))
async def tt(event):
    url = event.pattern_match.group(1)
    if not any(d in url for d in SUPPORTED):
        await event.edit("❌ платформа не поддерживается")
        return

    await event.edit("⏳ скачиваю...")

    with tempfile.TemporaryDirectory() as tmpdir:
        opts = {**YDL_OPTS, "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s")}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fp = ydl.prepare_filename(info)
                if not os.path.exists(fp):
                    fp = fp.rsplit(".", 1)[0] + ".mp4"
        except Exception as e:
            await event.edit(f"❌ yt-dlp: {e}")
            return

        if not os.path.exists(fp):
            await event.edit("❌ файл не найден")
            return

        if os.path.getsize(fp) / 1024 / 1024 > 2000:
            await event.edit("❌ файл >2 ГБ")
            return

        try:
            await client.send_file(
                event.chat_id,
                fp,
                supports_streaming=True,
                reply_to=event.id,
            )
            await event.delete()
        except Exception as e:
            await event.edit(f"❌ отправка: {e}")


async def main():
    await client.start()
    print("userbot запущен — пиши .tt [ссылка]")
    await client.run_until_disconnected()


threading.Thread(target=start_ping_server, daemon=True).start()
asyncio.run(main())
