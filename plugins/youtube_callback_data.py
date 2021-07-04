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
    userLastDownloadTime = user_time.get(message.chat.id)
    try:
        if userLastDownloadTime > datetime.now():
            wait_time = round((userLastDownloadTime - datetime.now()).total_seconds() / 60, 2)
            await message.reply_text(f"`Wait {wait_time} Minutes before next Request`")
            return
    except:
        pass

    url = message.text.strip()
    await message.reply_chat_action("typing")
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
    try:
        # Todo add webp image support in thumbnail by default not supported by pyrogram
        # https://www.youtube.com/watch?v=lTTajzrSkCw
        img = wget.download(thumbnail_url)
        im = Image.open(img).convert("RGB")
        output_directory = os.path.join(os.getcwd(), "downloads", str(message.chat.id))
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        thumb_image_path = f"{output_directory}.jpg"
        im.save(thumb_image_path,"jpeg")
        await message.reply_photo(thumb_image_path, caption=title, reply_markup=buttons)
        await sentm.delete()
    except Exception as e:
        print(e)
        try:
            thumbnail_url = "https://telegra.ph/file/ce37f8203e1903feed544.png"
            await message.reply_photo(thumbnail_url, caption=title, reply_markup=buttons)
        except Exception as e:
            await sentm.edit(
            f"<code>{e}</code> #Error")

@Client.on_callback_query()
async def catch_youtube_fmtid(c, m):
    cb_data = m.data
    if cb_data.startswith("ytdata||"):
        yturl = cb_data.split("||")[-1]
        format_id = cb_data.split("||")[-2]
        media_type = cb_data.split("||")[-3].strip()
        print(media_type)
        if media_type == 'audio':
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton(
                "Audio", callback_data=f"{media_type}||{format_id}||{yturl}"), InlineKeyboardButton("Document",
                                                                                                    callback_data=f"docaudio||{format_id}||{yturl}")]])
        else:
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton(
                "Video", callback_data=f"{media_type}||{format_id}||{yturl}"), InlineKeyboardButton("Document",
                                                                                                    callback_data=f"docvideo||{format_id}||{yturl}")]])

        await m.edit_message_reply_markup(buttons)

    else:
        raise ContinuePropagation


@Client.on_callback_query()
async def catch_youtube_dldata(c, q):
    cb_data = q.data.strip()
    #print(q.message.chat.id)
    # Callback Data Check
    yturl = cb_data.split("||")[-1]
    format_id = cb_data.split("||")[-2]
    thumb_image_path = "/app/downloads" + \
        "/" + str(q.message.chat.id) + ".jpg"
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
     #   print(thumb_image_path)
    if not cb_data.startswith(("video", "audio", "docaudio", "docvideo")):
        print("no data found")
        raise ContinuePropagation

    filext = "%(title)s.%(ext)s"
    userdir = os.path.join(os.getcwd(), "downloads", str(q.message.chat.id))

    if not os.path.isdir(userdir):
        os.makedirs(userdir)
    await q.edit_message_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton("Downloading...", callback_data="down")]]))
    filepath = os.path.join(userdir, filext)
    # await q.edit_message_reply_markup([[InlineKeyboardButton("Processing..")]])

    audio_command = [
        "youtube-dl",
        "-c",
        "--prefer-ffmpeg",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", format_id,
        "-o", filepath,
        yturl,

    ]

    video_command = [
        "youtube-dl",
        "-c",
        "--embed-subs",
        "-f", f"{format_id}+bestaudio",
        "-o", filepath,
        "--hls-prefer-ffmpeg", yturl]

    loop = asyncio.get_event_loop()

    med = None
    if cb_data.startswith("audio"):
        filename = await downloadaudiocli(audio_command)
        med = InputMediaAudio(
            media=filename,
            thumb=thumb_image_path,
            caption=os.path.basename(filename),
            title=os.path.basename(filename)
        )

    if cb_data.startswith("video"):
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

    if cb_data.startswith("docaudio"):
        filename = await downloadaudiocli(audio_command)
        med = InputMediaDocument(
            media=filename,
            thumb=thumb_image_path,
            caption=os.path.basename(filename),
        )

    if cb_data.startswith("docvideo"):
        filename = await downloadvideocli(video_command)
        dur = round(duration(filename))
        med = InputMediaDocument(
            media=filename,
            thumb=thumb_image_path,
            caption=os.path.basename(filename),
        )
    if med:
        loop.create_task(send_file(c, q, med, filename))
    else:
        print("med not found")


async def send_file(c, q, med, filename):
    print(med)
    try:
        await q.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("Uploading...", callback_data="down")]]))
        await c.send_chat_action(chat_id=q.message.chat.id, action="upload_document")
        # this one is not working
        await Client.send_video(q.message.chat.id, med)
    except Exception as e:
        print(e)
        await q.edit_message_text(e)
    finally:
        try:
            os.remove(filename)
            os.remove(thumb_image_path)
        except:
            pass
