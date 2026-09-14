import os, glob, asyncio, yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TAG = "@epic_india"

app = Client("epic_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call = PyTgCalls(app)

QUEUE = {} # chat_id: [ (filepath, title) ]

def download(query, is_video=False):
    q = query if query.startswith("http") else f"ytsearch1:{query}"
    fmt = 'best[height<=480][ext=mp4]/best' if is_video else 'bestaudio[ext=m4a]/bestaudio/best'
    if "instagram.com" in q: fmt = 'best'
    opts = {'format': fmt, 'noplaylist': True, 'outtmpl': '%(title).30s.%(ext)s', 'quiet': True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(q, download=True)
        if 'entries' in info: info = info['entries'][0]
        return ydl.prepare_filename(info), info.get('title','Unknown')

@app.on_message(filters.command("play"))
async def play(c, m: Message):
    if len(m.command) < 2:
        return await m.reply(f"Use: /play <song name>\n\n{TAG}")
    q = m.text.split(None, 1)[1]
    wait = await m.reply("⚡️ Downloading...")
    try:
        fp, title = download(q, False)
        chat_id = m.chat.id
        if chat_id not in QUEUE: QUEUE[chat_id] = []

        # Try to play, if already playing then add to queue
        try:
            await call.play(chat_id, MediaStream(fp))
            await wait.delete()
            await c.send_message(chat_id, f"▶️ Playing: {title}\n\n{TAG}")
        except:
            QUEUE[chat_id].append((fp, title))
            await wait.delete()
            await c.send_message(chat_id, f"➕ Queued: {title}\nPosition: {len(QUEUE[chat_id])}\n\n{TAG}")

        try: await m.delete()
        except: pass
    except Exception as e:
        await m.reply(f"❌ {e}\n\n{TAG}")

@app.on_message(filters.command(["skip", "next"]))
async def skip(c, m: Message):
    chat_id = m.chat.id
    try: await m.delete()
    except: pass
    try:
        if chat_id in QUEUE and QUEUE[chat_id]:
            fp, title = QUEUE[chat_id].pop(0)
            await call.play(chat_id, MediaStream(fp))
            await c.send_message(chat_id, f"⏭️ Skipped to: {title}\n\n{TAG}")
        else:
            await call.leave(chat_id)
            await c.send_message(chat_id, f"Queue empty, Left VC\n\n{TAG}")
    except Exception as e:
        await c.send_message(chat_id, f"❌ Nothing to skip\n\n{TAG}")

@app.on_message(filters.command("vplay"))
async def vplay(c, m: Message):
    if len(m.command) < 2:
        return await m.reply(f"Use: /vplay <video>\n\n{TAG}")
    q = m.text.split(None, 1)[1]
    wait = await m.reply("⚡️")
    try:
        fp, title = download(q, True)
        await call.play(m.chat.id, MediaStream(fp, video=True))
        try: await m.delete()
        except: pass
        await wait.delete()
        await c.send_message(m.chat.id, f"🎬 Playing: {title}\n\n{TAG}")
    except Exception as e:
        await m.reply(f"❌ {e}\n\n{TAG}")

@app.on_message(filters.command("stop"))
async def stop(c, m: Message):
    try:
        QUEUE[m.chat.id] = []
        await call.leave(m.chat.id)
        await c.send_message(m.chat.id, f"⏹️ Stopped & Cleared\n\n{TAG}")
    except:
        await c.send_message(m.chat.id, f"Nothing playing\n\n{TAG}")
    try: await m.delete()
    except: pass

@app.on_message(filters.command("refresh"))
async def refresh(c, m: Message):
    for f in glob.glob("*.mp3")+glob.glob("*.mp4")+glob.glob("*.m4a")+glob.glob("*.webm")+glob.glob("*.jpg"):
        try: os.remove(f)
        except: pass
    QUEUE.clear()
    await m.reply(f"♻️ Cleaned\n\n{TAG}")

async def main():
    await app.start()
    await call.start()
    print(f"Bot Started {TAG}")
    await asyncio.Event().wait()

asyncio.run(main())
