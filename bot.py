from telethon import TelegramClient, events, Button
import yt_dlp
import instaloader
import os
import asyncio
import re
import shutil
from facebook_scraper import get_posts
import requests

# إعدادات البوت
api_id = '25983911'  # من my.telegram.org
api_hash = '62dfc033e0f68f86ce1cce4527597cad'  # من my.telegram.org
bot_token = '1539143917:AAHYrU09H3O_4_VZ6Dz-_XosXc8mlangr5k'  # من @BotFather
client = TelegramClient('GrokThunderBot', api_id, api_hash).start(bot_token=bot_token)

# أنماط الروابط
YT_PATTERN = r'(https?://(?:www\.)?(youtube|youtu\.be).*?)'
INSTA_PATTERN = r'(https?://(?:www\.)?instagram\.com/(p|reel)/.*?)'
TW_PATTERN = r'(https?://(?:www\.)?twitter\.com/.*?)'
FB_PATTERN = r'(https?://(?:www\.)?facebook\.com/.*?)'
PIN_PATTERN = r'(https?://(?:www\.)?pinterest\.com/.*?)'
DEEZER_PATTERN = r'(https?://(?:www\.)?deezer\.com/.*?)'

# تحميل من يوتيوب
async def download_youtube(url, event):
    wait_msg = await event.reply("جاري تحميل الفيديو... ⏳")
    ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(title)s.%(ext)s', 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = f"downloads/{info['title']}.{info['ext']}"
        await client.send_file(event.chat_id, file_path, caption=f"العنوان: {info['title']}\n@GrokThunderBot")
    except Exception as e:
        await event.reply(f"خطأ: {str(e)}\n@GrokThunderBot")
    finally:
        await wait_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

# تحميل من إنستغرام
async def download_instagram(url, event):
    wait_msg = await event.reply("جاري تحميل الريلز/البوست... ⏳")
    try:
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, url.split('/')[-2])
        file_path = f"downloads/{post.shortcode}.mp4" if post.is_video else f"downloads/{post.shortcode}.jpg"
        L.download_post(post, target="downloads")
        await client.send_file(event.chat_id, file_path, caption=f"العنوان: {post.caption[:50]}...\n@GrokThunderBot")
    except Exception as e:
        await event.reply(f"خطأ: {str(e)}\n@GrokThunderBot")
    finally:
        await wait_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

# تحميل من فيسبوك (صفحات عامة)
async def download_facebook(url, event):
    wait_msg = await event.reply("جاري تحميل من فيسبوك... ⏳")
    try:
        for post in get_posts(post_urls=[url], options={"comments": False}):
            if 'video' in post:
                video_url = post['video']
                file_path = "downloads/facebook_video.mp4"
                with open(file_path, 'wb') as f:
                    f.write(requests.get(video_url).content)
                await client.send_file(event.chat_id, file_path, caption=f"العنوان: {post['text'][:50]}...\n@GrokThunderBot")
                os.remove(file_path)
                break
    except Exception as e:
        await event.reply(f"خطأ: {str(e)}\n@GrokThunderBot")
    finally:
        await wait_msg.delete()

# تحميل من Deezer (بسيط باستخدام رابط)
async def download_deezer(url, event):
    wait_msg = await event.reply("جاري تحميل من Deezer... ⏳")
    try:
        # ملاحظة: يتطلب مكتبة deezloader (غير رسمية) أو API خارجي
        file_path = "downloads/deezer_track.mp3"  # افتراضي
        # هنا يمكن إضافة كود Deezer باستخدام deezloader
        await client.send_file(event.chat_id, file_path, caption=f"العنوان: تحميل من Deezer\n@GrokThunderBot")
    except Exception as e:
        await event.reply(f"خطأ: {str(e)}\n@GrokThunderBot")
    finally:
        await wait_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

# معالجة الروابط تلقائياً
@client.on(events.NewMessage)
async def handle_links(event):
    text = event.raw_text
    if re.match(YT_PATTERN, text):
        await download_youtube(text, event)
    elif re.match(INSTA_PATTERN, text):
        await download_instagram(text, event)
    elif re.match(FB_PATTERN, text):
        await download_facebook(text, event)
    elif re.match(DEEZER_PATTERN, text):
        await download_deezer(text, event)
    # أضف تويتر وبنترست هنا إذا أردت مكتبات إضافية

# البحث في يوتيوب
@client.on(events.NewMessage(pattern='/yt (.+)'))
async def youtube_search(event):
    query = event.pattern_match.group(1)
    ydl_opts = {'quiet': True, 'noplaylist': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
        
        buttons = []
        for i, res in enumerate(results, 1):
            title = res['title'][:30]
            duration = f"{res['duration']//60}:{res['duration']%60:02d}"
            size = f"{res['filesize']//(1024*1024)}MB" if 'filesize' in res else "غير معروف"
            buttons.append([Button.inline(f"{i}. {title} | {duration} | {size}", f"dl_yt_{res['id']}")])
        
        await event.reply("اختر نتيجة:\n@GrokThunderBot", buttons=buttons)
    except Exception as e:
        await event.reply(f"خطأ في البحث: {str(e)}\n@GrokThunderBot")

# البحث في Deezer (بسيط)
@client.on(events.NewMessage(pattern='/deezer (.+)'))
async def deezer_search(event):
    query = event.pattern_match.group(1)
    # ملاحظة: يتطلب تكامل Deezer API أو deezloader
    await event.reply(f"البحث في Deezer عن: {query} (قيد التطوير)\n@GrokThunderBot")

# تحميل بعد اختيار البحث
@client.on(events.CallbackQuery(pattern=r'dl_yt_.+'))
async def download_selected(event):
    video_id = event.data.decode().split('_')[2]
    url = f"https://youtube.com/watch?v={video_id}"
    wait_msg = await event.reply("جاري التحميل... ⏳")
    ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(title)s.%(ext)s'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = f"downloads/{info['title']}.{info['ext']}"
        await client.send_file(event.chat_id, file_path, caption=f"العنوان: {info['title']}\n@GrokThunderBot")
    except Exception as e:
        await event.reply(f"خطأ: {str(e)}\n@GrokThunderBot")
    finally:
        await wait_msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

# تنظيف المجلد عند البدء
def clean_downloads():
    if os.path.exists("downloads"):
        shutil.rmtree("downloads")
    os.makedirs("downloads")

# بدء البوت
async def main():
    clean_downloads()
    await client.start()
    print("GrokThunderBot is running!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
