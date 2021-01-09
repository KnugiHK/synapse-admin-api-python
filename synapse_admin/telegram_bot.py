from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from synapse_admin import User, Management, Media, Room
import logging
import datetime

updater = Updater(token="")
dispatcher = updater.dispatcher

logtime = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
global filename
filename = "bot_log_" + logtime
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_commander = User()
server_commander = Management()
media_commander = Media()
room_commander = Room()

def user_lists(update, context):
    lists, total = user_commander.lists()
    msg = f"There are {total} users:\n"
    for i in lists:
        msg += f"{i['name']}\n"
    context.bot.send_message(chat_id=update.message.chat_id, text=msg)

list_user_handler = CommandHandler('user_lists', user_lists)
dispatcher.add_handler(list_user_handler)

updater.start_polling()