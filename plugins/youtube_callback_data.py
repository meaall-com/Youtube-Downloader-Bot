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
from helper.ytdlfunc import downloadvideocli, downloadaudiocli
from datetime import datetime, timedelta
from PIL import Image
from bot import user_time
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.ytdlfunc import extractYt, create_buttons
from config import youtube_next_fetch
import wget

ytregex = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"


@Client.on_message(Filters.regex(ytregex))
async def ytdl(_, message):
    url = message.text.strip()
    await message.reply_chat_action("typing")
    ids = message.chat.id
    messageid = message.message_id
    try:
        title, thumbnail_url, formats = extractYt(url)

        now = datetime.now()
        user_time[message.chat.id] = now + \
                                     timedelta(minutes=youtube_next_fetch)

    except Exception:
        await message.reply_text("`Failed To Fetch Youtube Data... 😔 \nPossible Youtube Blocked server ip \n#error`")
        return
    buttons = InlineKeyboardMarkup(list(create_buttons(formats)))
    sentm = await message.reply_text("Processing Youtube Url 🔎 🔎 🔎")
        # Todo add webp image support in thumbnail by default not supported by pyrogram
        # https://www.youtube.com/watch?v=lTTajzrSkCw
    img = wget.download(thumbnail_url)
    im = Image.open(img).convert("RGB")
    output_directory = os.path.join(os.getcwd(), "downloads", "thumb")
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    thumb_image_path = f"{output_directory}.jpg"
    im.save(thumb_image_path,"jpeg")
    await sentm.reply_photo(thumb_image_path) 

    #print(q.message.chat.id)
    # Callback Data Check
    yturl = url
    format_id = 243
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





     #   print(thumb_image_path)

    filext = "%(title)s.%(ext)s"
    userdir = os.path.join(os.getcwd(), "downloads", "thumb")

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
        "--hls-prefer-ffmpeg", url]

    loop = asyncio.get_event_loop()

    med = None
    if url:
        filename = await downloadvideocli(video_command)
        dur = round(duration(filename))
        med = InputMediaVideo(
            media=filename,
            duration=dur,
            width=width,
            height=height,
            thumb=thumb_image_path,
            caption=title,
            supports_streaming=True
        )
    



    print(filename)
    print(ids)
    print(med)
    print(messageid)




    await sentm.reply_chat_action("upload_video")


    await Client.edit_message_media(ids, messageid, med, filename)











    try:
        os.remove(filename)
        os.remove(thumb_image_path)
    except:
         pass
