import asyncio
import os

from pyrogram import (Client,
                      Filters,
                      InlineKeyboardButton,
                      InlineKeyboardMarkup,
                      ContinuePropagation,
                      InputMediaDocument,
                      InputMediaVideo,
                      InputMediaAudio)

from helper.ffmfunc import duration
from helper.ytdlfunc import downloadvideocli, downloadaudiocli, extractYt, create_buttons
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from datetime import datetime, timedelta
from bot import user_time
from config import youtube_next_fetch
import wget
import os
from PIL import Image



ytregex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"


@Client.on_message(Filters.regex(ytregex))
url = message.text.strip()
await message.reply_chat_action("typing")
try:
    title, thumbnail_url, formats = extractYt(url)

    now = datetime.now()
    user_time[message.chat.id] = now + \
                                     timedelta(minutes=youtube_next_fetch)
    if url:
        yturl = url
        format_id = int(243)
        media_type = 'video'
        print(media_type)
    else:
        raise ContinuePropagation
    #print(q.message.chat.id)
    # Callback Data Check
    yturl = url
    format_id = int(243)
    thumb_image_path = "/app/downloads" + \
        "/" + str(message.chat.id) + ".jpg"
    print(thumb_image_path)
    if os.path.exists(thumb_image_path):
        width = 0
        height = 0
        metadata = extractMetadata(createParser(thumb_image_path))
        #print(metadata)
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")
        img = Image.open(thumb_image_path)
        if cb_data.startswith(("audio", "docaudio", "docvideo")):
            img.resize((320, height))
        else:
            img.resize((90, height))
        img.save(thumb_image_path, "JPEG")
     #   print(thumb_image

    filext = "%(title)s.%(ext)s"
    userdir = os.path.join(os.getcwd(), "downloads", str(q.message.chat.id))

    if not os.path.isdir(userdir):
        os.makedirs(userdir)
        filepath = os.path.join(userdir, filext)
    # await q.edit_message_reply_markup([[InlineKeyboardButton("Processing..")]])
video_command = [
        "youtube-dl",
        "-c",
        "--embed-subs",
        "-f", f"{format_id}+bestaudio",
        "-o", filepath,
        "--hls-prefer-ffmpeg", yturl]
        
    loop = asyncio.get_event_loop()
if url:
filename = await downloadvideocli(video_command)
        dur = round(duration(filename))
        med = InputMediaVideo(
            media=filename,
            duration=dur,
            width=width,
            height=height,
            thumb=thumb_image_path,
            caption=os.path.basename(filename),
            supports_streaming=True
        )
    med = None

    loop.create_task(send_file(c, q, med, filename))

    print(med)
    try:
        # this one is not working
        await q.edit_message_media(media=med)
    except Exception as e:
        print(e)
        await q.edit_message_text(e)
    finally:
        try:
            os.remove(filename)
            os.remove(thumb_image_path)
        except:
            pass
