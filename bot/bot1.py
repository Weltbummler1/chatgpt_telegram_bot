from telegram.ext import ConversationHandler
import pandas as pd
import httpx
import tabulate
import requests
import openai_utils
import database
import config
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    AIORateLimiter,
    filters
)
from telegram import (
    Update,
    User,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
import telegram
import os
import logging
import asyncio
import traceback
import html
import json
import tempfile
import pydub
from pathlib import Path
from datetime import datetime
import openai
from telegram import Update
import locale
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, Filters)
from telegram import Update
from telegram.ext.callbackcontext import CallbackContext

locale.setlocale(locale.LC_ALL, '')
# Define constants for each state in the conversation
GET_ADULTS, GET_CHILDREN, GET_CHILDAGES, GET_ROOMS, GET_ARRIVAL_DATE, GET_DEPARTURE_DATE = range(
    6)


# setup
db = database.Database()
logger = logging.getLogger(__name__)

user_semaphores = {}
user_tasks = {}
CITY, DATE, ROOMS = range(3)

HELP_MESSAGE = """<b>DISCLAIMER:</b> I am super smart, but please be advised information given here are meant as guidance and not legally binding. Our team will confirm any prices and options suggest directly to you. 
"""

HELP_GROUP_CHAT_MESSAGE = """You can add bot to any <b>group chat</b> to help and entertain its participants!

Instructions (see <b>video</b> below):
1. Add the bot to the group chat
2. Make it an <b>admin</b>, so that it can see messages (all other rights can be restricted)
3. You're awesome!

To get a reply from the bot in the chat – @ <b>tag</b> it or <b>reply</b> to its message.
For example: "{bot_username} write a poem about Telegram"
"""


def split_text_into_chunks(text, chunk_size):
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


'''
async def hotel_booking_handle(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    state = db.get_user_attribute(user_id, "state")

    if state == "waiting_for_adults":
        adults = update.message.text
        db.set_user_attribute(user_id, "adults", adults)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the number of children:")
        db.set_user_attribute(user_id, "state", "waiting_for_children")

    elif state == "waiting_for_children":
        children = update.message.text
        db.set_user_attribute(user_id, "children", children)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the children's ages (separated by '|'):")
        db.set_user_attribute(user_id, "state", "waiting_for_childages")

    elif state == "waiting_for_childages":
        childages = update.message.text
        db.set_user_attribute(user_id, "childages", childages)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the number of rooms:")
        db.set_user_attribute(user_id, "state", "waiting_for_rooms")

    elif state == "waiting_for_rooms":
        rooms = update.message.text
        db.set_user_attribute(user_id, "rooms", rooms)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the arrival date (YYYY-MM-DD):")
        db.set_user_attribute(user_id, "state", "waiting_for_arrival_date")

    elif state == "waiting_for_arrival_date":
        arrival_date = update.message.text
        db.set_user_attribute(user_id, "arrival_date", arrival_date)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the departure date (YYYY-MM-DD):")
        db.set_user_attribute(user_id, "state", "waiting_for_departure_date")

    elif state == "waiting_for_departure_date":
        departure_date = update.message.text
        db.set_user_attribute(user_id, "departure_date", departure_date)

        await context.bot.send_message(chat_id=update.effective_chat.id, text="REALTIME Checking Hotel Availability and Prices for you. Please wait for the magic... 🪄", parse_mode='HTML')

        adults = db.get_user_attribute(user_id, "adults")
        children = db.get_user_attribute(user_id, "children")
        childages = db.get_user_attribute(user_id, "childages")
        rooms = db.get_user_attribute(user_id, "rooms")
        arrival_date = db.get_user_attribute(user_id, "arrival_date")
        departure_date = db.get_user_attribute(user_id, "departure_date")

        api_url = f"http://host.docker.internal:5000/scrape?arrive={arrival_date}&depart={departure_date}&adults={adults}&child={children}&childages={childages}&rooms={rooms}&hotel_id=64518&currency=IDR"
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
        hotel_data = response.json()

        headers = hotel_data[0].keys()
        table = tabulate.tabulate(hotel_data, headers='keys', tablefmt="grid")
        df = pd.DataFrame(hotel_data)
        exchange_rate = 0.000067  # Example exchange rate

        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Realtime Check done! ⚡</b> Here we go, your EOA Hotel Quote 🏨\n\n", parse_mode='HTML')
        message_intro = f"We got <b>{len(df)}</b> options for you:\n\n"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_intro, parse_mode='HTML')

        for _, row in df.iterrows():
            message = f"<b>Room Type:</b> {row['room_name']}\n"
            message += f"Rate Name: {row['rate_name']}\n"
            message += f"Rate Description:\n{row['rate_description']}\n\n"
            message += f"Nights: {row['nights']}\n"
            message += f"<b>Your EOA Price Per Night:</b> IDR {row['markup_price']:,}\n"
            message += f"Published Website Price IDR {row['price_per_night']:,}\n"
            message += f"<b>Your EOA Price Total:</b> IDR {row['total_markup_price']:,}\n\n"

            usd_price_per_night = int(row['markup_price'] * exchange_rate)
            usd_total_price = int(row['total_markup_price'] * exchange_rate)

            message += f"Estimated USD Price Per Night: USD {usd_price_per_night:,.2f}\n"
            message += f"<b>Estimated USD Price Total:</b> USD {usd_total_price:,.2f}\n\n"

            await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')

        db.set_user_attribute(user_id, "state", "")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the number of adults:")
        db.set_user_attribute(user_id, "state", "waiting_for_adults")

    
    if state == CITY:
        # Store the city and ask for the date
        db.set_user_attribute(user_id, "city", update.message.text)
        await update.message.reply_text("What date would you like to check in?")
        db.set_user_attribute(user_id, "state", DATE)
    elif state == DATE:
        # Store the date and ask for the number of rooms
        db.set_user_attribute(user_id, "date", update.message.text)
        await update.message.reply_text("How many rooms would you like to book?")
        db.set_user_attribute(user_id, "state", ROOMS)
    elif state == ROOMS:
        # Store the number of rooms and book the hotel
        db.set_user_attribute(user_id, "rooms", update.message.text)
        await update.message.reply_text("Booking hotel...")
        # Call your hotel booking API here with the collected data
        db.set_user_attribute(user_id, "state", None)  # Clear the state when done
        '''


# Define constants for each state in the conversation
GET_ADULTS, GET_CHILDREN, GET_CHILDAGES, GET_ROOMS, GET_ARRIVAL_DATE, GET_DEPARTURE_DATE = range(
    6)


async def start(update: Update, context: CallbackContext):
    update.message.reply_text('Please enter the number of adults:')
    return GET_ADULTS


async def get_adults(update: Update, context: CallbackContext):
    adults = update.message.text
    context.user_data['adults'] = adults
    update.message.reply_text('Please enter the number of children:')
    return GET_CHILDREN


async def get_children(update: Update, context: CallbackContext):
    children = update.message.text
    context.user_data['children'] = children
    update.message.reply_text(
        'Please enter the ages of the children (separated by "|"):')
    return GET_CHILDAGES


async def get_childages(update: Update, context: CallbackContext):
    childages = update.message.text
    context.user_data['childages'] = childages
    update.message.reply_text('Please enter the number of rooms:')
    return GET_ROOMS


async def get_rooms(update: Update, context: CallbackContext):
    rooms = update.message.text
    context.user_data['rooms'] = rooms
    update.message.reply_text('Please enter the arrival date (YYYY-MM-DD):')
    return GET_ARRIVAL_DATE


async def get_arrival_date(update: Update, context: CallbackContext):
    arrival_date = update.message.text
    context.user_data['arrival_date'] = arrival_date
    update.message.reply_text('Please enter the departure date (YYYY-MM-DD):')
    return GET_DEPARTURE_DATE


async def get_departure_date(update: Update, context: CallbackContext):
    departure_date = update.message.text
    context.user_data['departure_date'] = departure_date
    return process_booking(update, context)


async def process_booking(update: Update, context: CallbackContext):
    # Process the data collected from the user
    adults = context.user_data['adults']
    children = context.user_data['children']
    childages = context.user_data['childages']
    rooms = context.user_data['rooms']
    arrival_date = context.user_data['arrival_date']
    departure_date = context.user_data['departure_date']
    api_url = f"http://host.docker.internal:5000/scrape?arrive={arrival_date}&depart={departure_date}&adults={adults}&child={children}&childages={childages}&rooms={rooms}&hotel_id=64518&currency=IDR"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
    hotel_data = response.json()

    headers = hotel_data[0].keys()
    table = tabulate.tabulate(hotel_data, headers='keys', tablefmt="grid")
    df = pd.DataFrame(hotel_data)
    exchange_rate = 0.000067  # Example exchange rate

    await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>Realtime Check done! ⚡</b> Here we go, your EOA Hotel Quote 🏨\n\n", parse_mode='HTML')
    message_intro = f"We got <b>{len(df)}</b> options for you:\n\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message_intro, parse_mode='HTML')

    for _, row in df.iterrows():
        message = f"<b>Room Type:</b> {row['room_name']}\n"
        message += f"Rate Name: {row['rate_name']}\n"
        message += f"Rate Description:\n{row['rate_description']}\n\n"
        message += f"Nights: {row['nights']}\n"
        message += f"<b>Your EOA Price Per Night:</b> IDR {row['markup_price']:,}\n"
        message += f"Published Website Price IDR {row['price_per_night']:,}\n"
        message += f"<b>Your EOA Price Total:</b> IDR {row['total_markup_price']:,}\n\n"

        usd_price_per_night = int(row['markup_price'] * exchange_rate)
        usd_total_price = int(row['total_markup_price'] * exchange_rate)

        message += f"Estimated USD Price Per Night: USD {usd_price_per_night:,.2f}\n"
        message += f"<b>Estimated USD Price Total:</b> USD {usd_total_price:,.2f}\n\n"

        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Booking process cancelled.')
    return ConversationHandler.END


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('bookhotel', start)],
    states={
        GET_ADULTS: [MessageHandler(Filters.text & ~Filters.command, get_adults)],
        GET_CHILDREN: [MessageHandler(Filters.text & ~Filters.command, get_children)],
        GET_CHILDAGES: [MessageHandler(Filters.text & ~Filters.command, get_childages)],
        GET_ROOMS: [MessageHandler(Filters.text & ~Filters.command, get_rooms)],
        GET_ARRIVAL_DATE: [MessageHandler(Filters.text & ~Filters.command, get_arrival_date)],
        GET_DEPARTURE_DATE: [MessageHandler(Filters.text & ~Filters.command, get_departure_date)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

application.add_handler(conversation_handler)


async def register_user_if_not_exists(update: Update, context: CallbackContext, user: User):
    if not db.check_if_user_exists(user.id):
        db.add_new_user(
            user.id,
            update.message.chat_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        db.start_new_dialog(user.id)

    if db.get_user_attribute(user.id, "current_dialog_id") is None:
        db.start_new_dialog(user.id)

    if user.id not in user_semaphores:
        user_semaphores[user.id] = asyncio.Semaphore(1)

    if db.get_user_attribute(user.id, "current_model") is None:
        db.set_user_attribute(user.id, "current_model",
                              config.models["available_text_models"][0])

    # back compatibility for n_used_tokens field
    n_used_tokens = db.get_user_attribute(user.id, "n_used_tokens")
    if isinstance(n_used_tokens, int) or isinstance(n_used_tokens, float):  # old format
        new_n_used_tokens = {
            "gpt-3.5-turbo": {
                "n_input_tokens": 0,
                "n_output_tokens": n_used_tokens
            }
        }
        db.set_user_attribute(user.id, "n_used_tokens", new_n_used_tokens)

    # voice message transcription
    if db.get_user_attribute(user.id, "n_transcribed_seconds") is None:
        db.set_user_attribute(user.id, "n_transcribed_seconds", 0.0)

    # image generation
    if db.get_user_attribute(user.id, "n_generated_images") is None:
        db.set_user_attribute(user.id, "n_generated_images", 0)


async def is_bot_mentioned(update: Update, context: CallbackContext):
    try:
        message = update.message

        if message.chat.type == "private":
            return True

        if message.text is not None and ("@" + context.bot.username) in message.text:
            return True

        if message.reply_to_message is not None:
            if message.reply_to_message.from_user.id == context.bot.id:
                return True
    except:
        return True
    else:
        return False


async def start_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id

    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    db.start_new_dialog(user_id)
    user_first_name = update.message.from_user.first_name  # Get the user's first name
    username = update.message.from_user.username  # Get the user's username
    user_first_name = update.message.from_user.first_name or "there"

    # Send an image
    with open('eoa.jpg', 'rb') as photo:
        await update.message.reply_photo(photo=photo)

    reply_text = f"Hi <b>{username}</b>!\n\nI'm your <b>Essence of Asia</b> B2B travel agent bot 💛 powered by the world's smartest AI - ChatGPT 🤖\n\nI can assist you in finding the best available travel options for your clients. Luxury Hotels and Experience are my expertise.\n\nI speak <b>ALL</b> languages 🇷🇺🇬🇧🇫🇷🇩🇪🇪🇸🇮🇹\nYou can send Voice Messages instead of text 🎤\n\nType /human at any time, if you want to chat with our team 🫶\n\n"
    reply_text += HELP_MESSAGE

    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)
    await show_chat_modes_handle(update, context)


# async def forward_to_support_group(update: Update, context: CallbackContext):
#    support_group_chat_id = -1001609358922  # replace with your group's chat ID
#    await context.bot.forward_message(chat_id=support_group_chat_id, from_chat_id=update.message.chat_id, message_id=update.message.message_id)


async def get_chat_id(update: Update, context: CallbackContext):
    print(update.message.chat.id)


async def help_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())
    await update.message.reply_text(HELP_MESSAGE, parse_mode=ParseMode.HTML)


async def help_group_chat_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text = HELP_GROUP_CHAT_MESSAGE.format(
        bot_username="@" + context.bot.username)

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await update.message.reply_video(config.help_group_chat_video_path)


async def send_channel_message(update: Update, context: CallbackContext):
    await update.message.reply_text("Speak to our team directly at https://t.me/Essence_Of_Asia")


async def create_channel_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Chat with our team directly",
                                 url="https://t.me/Essence_Of_Asia")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def retry_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    dialog_messages = db.get_dialog_messages(user_id, dialog_id=None)
    if len(dialog_messages) == 0:
        await update.message.reply_text("No message to retry 🤷‍♂️")
        return

    last_dialog_message = dialog_messages.pop()
    # last message was removed from the context
    db.set_dialog_messages(user_id, dialog_messages, dialog_id=None)

    await message_handle(update, context, message=last_dialog_message["user"], use_new_dialog_timeout=False)


async def message_handle(update: Update, context: CallbackContext, message=None, use_new_dialog_timeout=True):
    # check if bot was mentioned (for group chats)
    if not await is_bot_mentioned(update, context):
        return

    # check if message is edited
    if update.edited_message is not None:
        await edited_message_handle(update, context)
        return

    _message = message or update.message.text

    # remove bot mention (in group chats)
    if update.message.chat.type != "private":
        _message = _message.replace("@" + context.bot.username, "").strip()

    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    chat_mode = db.get_user_attribute(user_id, "current_chat_mode")

    if chat_mode == "artist":
        await generate_image_handle(update, context, message=message)
        return

    handled = await hotel_booking_handle(update, context)
    if handled:
        return

    user_id = update.message.from_user.id
    state = db.get_user_attribute(user_id, "state")
    if state in [CITY, DATE, ROOMS]:
        return

    async def message_handle_fn():
        # new dialog timeout
        if use_new_dialog_timeout:
            if (datetime.now() - db.get_user_attribute(user_id, "last_interaction")).seconds > config.new_dialog_timeout and len(db.get_dialog_messages(user_id)) > 0:
                db.start_new_dialog(user_id)
                await update.message.reply_text(f"Starting new dialog due to timeout (<b>{config.chat_modes[chat_mode]['name']}</b> mode) ✅", parse_mode=ParseMode.HTML)
        db.set_user_attribute(user_id, "last_interaction", datetime.now())

        # in case of CancelledError
        n_input_tokens, n_output_tokens = 0, 0
        current_model = db.get_user_attribute(user_id, "current_model")

        try:
            # send placeholder message to user
            placeholder_message = await update.message.reply_text("...")

            # send typing action
            await update.message.chat.send_action(action="typing")

            if _message is None or len(_message) == 0:
                await update.message.reply_text("🥲 You sent <b>empty message</b>. Please, try again!", parse_mode=ParseMode.HTML)
                return

            dialog_messages = db.get_dialog_messages(user_id, dialog_id=None)
            parse_mode = {
                "html": ParseMode.HTML,
                "markdown": ParseMode.MARKDOWN
            }[config.chat_modes[chat_mode]["parse_mode"]]

            chatgpt_instance = openai_utils.ChatGPT(model=current_model)
            if config.enable_message_streaming:
                gen = chatgpt_instance.send_message_stream(
                    _message, dialog_messages=dialog_messages, chat_mode=chat_mode)
            else:
                answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed = await chatgpt_instance.send_message(
                    _message,
                    dialog_messages=dialog_messages,
                    chat_mode=chat_mode
                )
                support_group_chat_id = -1001609358922  # replace with your group's chat ID
                await context.bot.forward_message(chat_id=support_group_chat_id, from_chat_id=message.chat_id, message_id=message.message_id)

                async def fake_gen():
                    yield "finished", answer, (n_input_tokens, n_output_tokens), n_first_dialog_messages_removed

                gen = fake_gen()

            prev_answer = ""
            async for gen_item in gen:
                status, answer, (n_input_tokens,
                                 n_output_tokens), n_first_dialog_messages_removed = gen_item

                answer = answer[:4096]  # telegram message limit

                # update only when 100 new symbols are ready
                if abs(len(answer) - len(prev_answer)) < 100 and status != "finished":
                    continue

                try:
                    await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id, parse_mode=parse_mode)
                except telegram.error.BadRequest as e:
                    if str(e).startswith("Message is not modified"):
                        continue
                    else:
                        await context.bot.edit_message_text(answer, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id)

                await asyncio.sleep(0.01)  # wait a bit to avoid flooding

                prev_answer = answer

            # update user data
            new_dialog_message = {"user": _message,
                                  "bot": answer, "date": datetime.now()}
            db.set_dialog_messages(
                user_id,
                db.get_dialog_messages(
                    user_id, dialog_id=None) + [new_dialog_message],
                dialog_id=None
            )

            db.update_n_used_tokens(
                user_id, current_model, n_input_tokens, n_output_tokens)

        except asyncio.CancelledError:
            # note: intermediate token updates only work when enable_message_streaming=True (config.yml)
            db.update_n_used_tokens(
                user_id, current_model, n_input_tokens, n_output_tokens)
            raise

        except Exception as e:
            error_text = f"Something went wrong during completion. Reason: {e}"
            logger.error(error_text)
            await update.message.reply_text(error_text)
            return

        # send message if some messages were removed from the context
        if n_first_dialog_messages_removed > 0:
            if n_first_dialog_messages_removed == 1:
                text = "✍️ <i>Note:</i> Your current dialog is too long, so your <b>first message</b> was removed from the context.\n Send /new command to start new dialog"
            else:
                text = f"✍️ <i>Note:</i> Your current dialog is too long, so <b>{n_first_dialog_messages_removed} first messages</b> were removed from the context.\n Send /new command to start new dialog"
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    # await forward_to_support_group(update, context)

    async with user_semaphores[user_id]:
        task = asyncio.create_task(message_handle_fn())
        user_tasks[user_id] = task

        try:
            await task
        except asyncio.CancelledError:
            await update.message.reply_text("✅ Canceled", parse_mode=ParseMode.HTML)
        else:
            pass
        finally:
            if user_id in user_tasks:
                del user_tasks[user_id]


async def is_previous_message_not_answered_yet(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)

    user_id = update.message.from_user.id
    if user_semaphores[user_id].locked():
        text = "⏳ Please <b>wait</b> for a reply to the previous message\n"
        text += "Or you can /cancel it"
        await update.message.reply_text(text, reply_to_message_id=update.message.id, parse_mode=ParseMode.HTML)
        return True
    else:
        return False


async def voice_message_handle(update: Update, context: CallbackContext):
    # check if bot was mentioned (for group chats)
    if not await is_bot_mentioned(update, context):
        return

    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    voice = update.message.voice
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        voice_ogg_path = tmp_dir / "voice.ogg"

        # download
        voice_file = await context.bot.get_file(voice.file_id)
        await voice_file.download_to_drive(voice_ogg_path)

        # convert to mp3
        voice_mp3_path = tmp_dir / "voice.mp3"
        pydub.AudioSegment.from_file(voice_ogg_path).export(
            voice_mp3_path, format="mp3")

        # transcribe
        with open(voice_mp3_path, "rb") as f:
            transcribed_text = await openai_utils.transcribe_audio(f)

            if transcribed_text is None:
                transcribed_text = ""

    text = f"🎤: <i>{transcribed_text}</i>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

    # update n_transcribed_seconds
    db.set_user_attribute(user_id, "n_transcribed_seconds", voice.duration +
                          db.get_user_attribute(user_id, "n_transcribed_seconds"))

    await message_handle(update, context, message=transcribed_text)


async def generate_image_handle(update: Update, context: CallbackContext, message=None):
    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    await update.message.chat.send_action(action="upload_photo")

    message = message or update.message.text

    try:
        image_urls = await openai_utils.generate_images(message, n_images=config.return_n_generated_images)
    except openai.error.InvalidRequestError as e:
        if str(e).startswith("Your request was rejected as a result of our safety system"):
            text = "🥲 Your request <b>doesn't comply</b> with OpenAI's usage policies.\nWhat did you write there, huh?"
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
            return
        else:
            raise

    # token usage
    db.set_user_attribute(user_id, "n_generated_images", config.return_n_generated_images +
                          db.get_user_attribute(user_id, "n_generated_images"))

    for i, image_url in enumerate(image_urls):
        await update.message.chat.send_action(action="upload_photo")
        await update.message.reply_photo(image_url, parse_mode=ParseMode.HTML)


async def new_dialog_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    db.start_new_dialog(user_id)
    await update.message.reply_text("Starting new dialog ✅")

    chat_mode = db.get_user_attribute(user_id, "current_chat_mode")
    await update.message.reply_text(f"{config.chat_modes[chat_mode]['welcome_message']}", parse_mode=ParseMode.HTML)


async def cancel_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    if user_id in user_tasks:
        task = user_tasks[user_id]
        task.cancel()
    else:
        await update.message.reply_text("<i>Nothing to cancel...</i>", parse_mode=ParseMode.HTML)


def get_chat_mode_menu(page_index: int):
    n_chat_modes_per_page = config.n_chat_modes_per_page
    text = f"Select your <b>assistant</b> ({len(config.chat_modes)} modes available):"

    # buttons
    chat_mode_keys = list(config.chat_modes.keys())
    page_chat_mode_keys = chat_mode_keys[page_index *
                                         n_chat_modes_per_page:(page_index + 1) * n_chat_modes_per_page]

    keyboard = []
    for chat_mode_key in page_chat_mode_keys:
        name = config.chat_modes[chat_mode_key]["name"]
        keyboard.append([InlineKeyboardButton(
            name, callback_data=f"set_chat_mode|{chat_mode_key}")])

    # pagination
    if len(chat_mode_keys) > n_chat_modes_per_page:
        is_first_page = (page_index == 0)
        is_last_page = ((page_index + 1) *
                        n_chat_modes_per_page >= len(chat_mode_keys))

        if is_first_page:
            keyboard.append([
                InlineKeyboardButton(
                    "»", callback_data=f"show_chat_modes|{page_index + 1}")
            ])
        elif is_last_page:
            keyboard.append([
                InlineKeyboardButton(
                    "«", callback_data=f"show_chat_modes|{page_index - 1}"),
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    "«", callback_data=f"show_chat_modes|{page_index - 1}"),
                InlineKeyboardButton(
                    "»", callback_data=f"show_chat_modes|{page_index + 1}")
            ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    return text, reply_markup


async def show_chat_modes_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text, reply_markup = get_chat_mode_menu(0)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def show_chat_modes_callback_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update.callback_query, context, update.callback_query.from_user)
    if await is_previous_message_not_answered_yet(update.callback_query, context):
        return

    user_id = update.callback_query.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    query = update.callback_query
    await query.answer()

    page_index = int(query.data.split("|")[1])
    if page_index < 0:
        return

    text, reply_markup = get_chat_mode_menu(page_index)
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except telegram.error.BadRequest as e:
        if str(e).startswith("Message is not modified"):
            pass


async def set_chat_mode_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update.callback_query, context, update.callback_query.from_user)
    user_id = update.callback_query.from_user.id

    query = update.callback_query
    await query.answer()

    chat_mode = query.data.split("|")[1]

    db.set_user_attribute(user_id, "current_chat_mode", chat_mode)
    db.start_new_dialog(user_id)

    await context.bot.send_message(
        update.callback_query.message.chat.id,
        f"{config.chat_modes[chat_mode]['welcome_message']}",
        parse_mode=ParseMode.HTML
    )

    support_group_chat_id = -1001609358922  # replace with your group's chat ID
    await context.bot.forward_message(chat_id=support_group_chat_id, from_chat_id=message.chat_id, message_id=message.message_id)


def get_settings_menu(user_id: int):
    current_model = db.get_user_attribute(user_id, "current_model")
    text = config.models["info"][current_model]["description"]

    text += "\n\n"
    score_dict = config.models["info"][current_model]["scores"]
    for score_key, score_value in score_dict.items():
        text += "🟢" * score_value + "⚪️" * \
            (5 - score_value) + f" – {score_key}\n\n"

    text += "\nSelect <b>model</b>:"

    # buttons to choose models
    buttons = []
    for model_key in config.models["available_text_models"]:
        title = config.models["info"][model_key]["name"]
        if model_key == current_model:
            title = "✅ " + title

        buttons.append(
            InlineKeyboardButton(
                title, callback_data=f"set_settings|{model_key}")
        )
    reply_markup = InlineKeyboardMarkup([buttons])

    return text, reply_markup


async def settings_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)
    if await is_previous_message_not_answered_yet(update, context):
        return

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    text, reply_markup = get_settings_menu(user_id)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def set_settings_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update.callback_query, context, update.callback_query.from_user)
    user_id = update.callback_query.from_user.id

    query = update.callback_query
    await query.answer()

    _, model_key = query.data.split("|")
    db.set_user_attribute(user_id, "current_model", model_key)
    db.start_new_dialog(user_id)

    text, reply_markup = get_settings_menu(user_id)
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except telegram.error.BadRequest as e:
        if str(e).startswith("Message is not modified"):
            pass


async def show_balance_handle(update: Update, context: CallbackContext):
    await register_user_if_not_exists(update, context, update.message.from_user)

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    # count total usage statistics
    total_n_spent_dollars = 0
    total_n_used_tokens = 0

    n_used_tokens_dict = db.get_user_attribute(user_id, "n_used_tokens")
    n_generated_images = db.get_user_attribute(user_id, "n_generated_images")
    n_transcribed_seconds = db.get_user_attribute(
        user_id, "n_transcribed_seconds")

    details_text = "🏷️ Details:\n"
    for model_key in sorted(n_used_tokens_dict.keys()):
        n_input_tokens, n_output_tokens = n_used_tokens_dict[model_key][
            "n_input_tokens"], n_used_tokens_dict[model_key]["n_output_tokens"]
        total_n_used_tokens += n_input_tokens + n_output_tokens

        n_input_spent_dollars = config.models["info"][model_key]["price_per_1000_input_tokens"] * (
            n_input_tokens / 1000)
        n_output_spent_dollars = config.models["info"][model_key]["price_per_1000_output_tokens"] * (
            n_output_tokens / 1000)
        total_n_spent_dollars += n_input_spent_dollars + n_output_spent_dollars

        details_text += f"- {model_key}: <b>{n_input_spent_dollars + n_output_spent_dollars:.03f}$</b> / <b>{n_input_tokens + n_output_tokens} tokens</b>\n"

    # image generation
    image_generation_n_spent_dollars = config.models["info"][
        "dalle-2"]["price_per_1_image"] * n_generated_images
    if n_generated_images != 0:
        details_text += f"- DALL·E 2 (image generation): <b>{image_generation_n_spent_dollars:.03f}$</b> / <b>{n_generated_images} generated images</b>\n"

    total_n_spent_dollars += image_generation_n_spent_dollars

    # voice recognition
    voice_recognition_n_spent_dollars = config.models["info"]["whisper"]["price_per_1_min"] * (
        n_transcribed_seconds / 60)
    if n_transcribed_seconds != 0:
        details_text += f"- Whisper (voice recognition): <b>{voice_recognition_n_spent_dollars:.03f}$</b> / <b>{n_transcribed_seconds:.01f} seconds</b>\n"

    total_n_spent_dollars += voice_recognition_n_spent_dollars

    text = f"You spent <b>{total_n_spent_dollars:.03f}$</b>\n"
    text += f"You used <b>{total_n_used_tokens}</b> tokens\n\n"
    text += details_text

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def edited_message_handle(update: Update, context: CallbackContext):
    if update.edited_message.chat.type == "private":
        text = "🥲 Unfortunately, message <b>editing</b> is not supported"
        await update.edited_message.reply_text(text, parse_mode=ParseMode.HTML)


async def error_handle(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    try:
        # collect error message
        tb_list = traceback.format_exception(
            None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f"An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )

        # split text into multiple messages due to 4096 character limit
        for message_chunk in split_text_into_chunks(message, 4096):
            try:
                await context.bot.send_message(update.effective_chat.id, message_chunk, parse_mode=ParseMode.HTML)
                support_group_chat_id = -1001609358922  # replace with your group's chat ID
                await context.bot.forward_message(chat_id=support_group_chat_id, from_chat_id=message.chat_id, message_id=message.message_id)
            except telegram.error.BadRequest:
                # answer has invalid characters, so we send it without parse_mode
                await context.bot.send_message(update.effective_chat.id, message_chunk)
    except:
        await context.bot.send_message(update.effective_chat.id, "Some error in error handler")


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/new", "Start new dialog"),
        BotCommand("/mode", "Select chat mode"),
        BotCommand("/retry", "Re-generate response for previous query"),
        BotCommand("/balance", "Show balance"),
        BotCommand("/settings", "Show settings"),
        BotCommand("/help", "Show help message"),
        BotCommand("/human", "Chat with us direvtly"),
        BotCommand("/get_chat_id", "Get chat id"),
        BotCommand("/start", "Restart the bot")
    ])


async def book_hotel_handle(update: Update, context: CallbackContext):

    # Register the user if not exists
    await register_user_if_not_exists(update, context, update.message.from_user)

    user_id = update.message.from_user.id
    db.set_user_attribute(user_id, "last_interaction", datetime.now())

    # Ask for the city
    await update.message.reply_text("Which city would you like to book a hotel in?")

    # Set the conversation state to CITY
    db.set_user_attribute(user_id, "state", CITY)


def run_bot() -> None:
    application = (
        ApplicationBuilder()
        .token(config.telegram_token)
        .concurrent_updates(True)
        .rate_limiter(AIORateLimiter(max_retries=5))
        .http_version("1.1")
        .get_updates_http_version("1.1")
        .post_init(post_init)
        .build()
    )

    # add handlers
    user_filter = filters.ALL
    if len(config.allowed_telegram_usernames) > 0:
        usernames = [
            x for x in config.allowed_telegram_usernames if isinstance(x, str)]
        any_ids = [
            x for x in config.allowed_telegram_usernames if isinstance(x, int)]
        user_ids = [x for x in any_ids if x > 0]
        group_ids = [x for x in any_ids if x < 0]
        user_filter = filters.User(username=usernames) | filters.User(
            user_id=user_ids) | filters.Chat(chat_id=group_ids)

    application.add_handler(CommandHandler("get_chat_id", get_chat_id))
    application.add_handler(CommandHandler(
        "human", send_channel_message, filters=user_filter))

    # High priority for hotel_booking_handle to match numbers in response to questions
    # application.add_handler(MessageHandler(filters.Regex(
    #    r'^[0-9]+$') & filters.TEXT & ~filters.COMMAND & user_filter, hotel_booking_handle), group=1)

    application.add_handler(MessageHandler(filters.Regex(
        r'book hotel') & filters.TEXT & ~filters.COMMAND & user_filter, book_hotel_handle))
    application.add_handler(MessageHandler(filters.Regex(
        r'bookhotel') & filters.TEXT & ~filters.COMMAND & user_filter, hotel_booking_handle))

    application.add_handler(CommandHandler(
        "start", start_handle, filters=user_filter))
    application.add_handler(CommandHandler(
        "help", help_handle, filters=user_filter))
    application.add_handler(CommandHandler(
        "help_group_chat", help_group_chat_handle, filters=user_filter))

    # Lower priority for message_handle to match all other text messages
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & user_filter, message_handle), group=2)

    application.add_handler(CommandHandler(
        "retry", retry_handle, filters=user_filter))
    application.add_handler(CommandHandler(
        "new", new_dialog_handle, filters=user_filter))
    application.add_handler(CommandHandler(
        "cancel", cancel_handle, filters=user_filter))

    application.add_handler(MessageHandler(
        filters.VOICE & user_filter, voice_message_handle))
    application.add_handler(CommandHandler(
        "mode", show_chat_modes_handle, filters=user_filter))
    application.add_handler(CallbackQueryHandler(
        show_chat_modes_callback_handle, pattern="^show_chat_modes"))
    application.add_handler(CallbackQueryHandler(
        set_chat_mode_handle, pattern="^set_chat_mode"))

    application.add_handler(CommandHandler(
        "settings", settings_handle, filters=user_filter))
    application.add_handler(CallbackQueryHandler(
        set_settings_handle, pattern="^set_settings"))

    application.add_handler(CommandHandler(
        "balance", show_balance_handle, filters=user_filter))

    application.add_error_handler(error_handle)

    # start the bot
    application.run_polling()


if __name__ == "__main__":
    run_bot()