import logging
import os
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from readFile import *
from uuid import uuid4
import helpTexts as ht
import log as lg
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def help_command(update, context):
    update.message.reply_html(ht.helpText)


def createUniversityKeyboard():
    university = getAllUniversities()
    keyboard = []
    for uni in university:
        keyboard.append([InlineKeyboardButton(uni, callback_data=uni)])
    return InlineKeyboardMarkup(keyboard)


def createSemesterKeyboard(context):
    semesters = getAllSemesterOfUniversity(getResponseData(context, 0))
    keyboard = []
    for sem in semesters:
        keyboard.append([InlineKeyboardButton(sem, callback_data=sem)])
    return InlineKeyboardMarkup(keyboard)


def createCourseKeyboard(context):
    courses = getAllCourseOfSemester(context)
    keyboard = []
    for course in courses:
        keyboard.append([InlineKeyboardButton(course, callback_data=course)])
    return InlineKeyboardMarkup(keyboard)


def sendTimeTable(context, update):
    data = getTimeTable(context)
    dataString = ""
    dataList = []
    for i, j in enumerate(data):
        if i == 0:
            heading = f"<b><u>{j['University']} {j['Course']} - Time Table </u></b>\n\n🎓 University - <b>{j['University']}</b>\n📚 Course - <b>{j['Course']}</b>\n📖 Semester - <b>{j['Sem']}</b>\n\n"
            dataString += heading

        singleData = f"📝 Subject Name - <b>{j['SubjectName']}</b>\n🗓️ Exam Date - <b>{j['Date']}</b>\n⏰ Exam Time - <b>{j['Time']}</b>\n❓ QP Code - <b>{j['QPCode']}</b>\n\n\n"
        dataString += singleData
        if i != 0 and i % 10 == 0:
            dataList.append(dataString)
            dataString = ""
    if(dataString):
        dataList.append(dataString)

    if len(dataList) == 0:
        update.callback_query.edit_message_text(dataString, parse_mode="HTML")
        update.callback_query.message.reply_html(
            ht.footer, disable_web_page_preview=True)
        lg.addToLog(context, update)
    else:
        update.callback_query.message.delete()
        for i in dataList:
            update.callback_query.message.reply_html(i)
        update.callback_query.message.reply_html(
            ht.footer, disable_web_page_preview=True)
        lg.addToLog(context, update)


help_keyboard = [[InlineKeyboardButton(
    "Join Channel", url="t.me/kslustudentshub")]]
help_reply_markup = InlineKeyboardMarkup(help_keyboard)


def start(update, context):
    context.bot.send_chat_action(
        chat_id=update.message.chat_id, action="typing")
    user = update.message.from_user
    channel_member = context.bot.get_chat_member(
        os.environ.get("CHANNEL_ID"), user_id=update.message.chat_id)
    status = channel_member["status"]
    lg.startLog(update, context, status)
    if(status == 'left'):
        update.message.reply_html(
            text=f"Hi {user.first_name}👋🏻, to use me(Bot🤖) you have to be a member of the Law_Timetable channel in order to stay updated with the latest updates.\n\n<b>Please click below button to join and then /start the bot again.</b>", reply_markup=help_reply_markup)
        return
    else:
        update.message.reply_text(
            'Choose Your 🎓University ⬇️', reply_markup=createUniversityKeyboard())


contactString = "For any clarification/feedback/report Email- info.lawtimetable@gmail.com"


def contactus(update, context):
    update.message.reply_html(contactString, disable_web_page_preview=True)


def end(update, context):
    context.user_data.clear()
    update.callback_query.message.delete()
    update.callback_query.message.reply_text(
        'if you want again, send /start command')
    update.callback_query.message.reply_text(
        'If its not working please report us use /contact to get contact details')


def getResponseData(context, position):
    return context.user_data.get(list(context.user_data.keys())[position])


def callBackQuery(update, context):
    query_data = update.callback_query.data
    key = str(uuid4())
    context.user_data[key] = query_data
    print(context.user_data)
    update.callback_query.answer()
    try:
        if query_data in getAllUniversities():
            update.callback_query.edit_message_text(
                'Choose Your 📖Semester⬇️', reply_markup=createSemesterKeyboard(context))

        elif len(context.user_data) == 2 and query_data in getAllSemesterOfUniversity(getResponseData(context, 0)):
            update.callback_query.edit_message_text(
                'Choose Your 📚Course⬇️', reply_markup=createCourseKeyboard(context))

        elif len(context.user_data) == 3 and query_data in getAllCourseOfSemester(context):
            sendTimeTable(context, update)
            context.user_data.clear()
            update.callback_query.message.reply_text(
                'if you want again send /start')

        if len(context.user_data) > 3:
            end(update, context)

    except Exception as e:
        print(str(e))
        end(update, context)


def getTimeTablefromQPCode(update, context):
    context.bot.send_chat_action(
        chat_id=update.message.chat_id, action="typing")
    user = update.message.from_user
    channel_member = context.bot.get_chat_member(
        os.environ.get("CHANNEL_ID"), user_id=update.message.chat_id)
    status = channel_member["status"]
    if(status == 'left'):
        update.message.reply_html(
            text=f"Hi {user.first_name}👋🏻, to use me(Bot🤖) you have to be a member of the Law_Timetable channel in order to stay updated with the latest updates.\n\n<b>Please click below button to join and then /start the bot again.</b>", reply_markup=help_reply_markup)
        return
    else:
        query = update.message.text[8:].split(' ')
        context.bot.send_chat_action(
            chat_id=update.message.chat_id, action="typing")
        if len(query[0]) == 0:
            qpText = f"Please enter QPCode after /qpcode command\nCheck /help if you have doubt or to know more"
            update.message.reply_text(qpText)
            return
        try:
            data = getTimeTablebyQPCode(query[0])
            if(len(data) == 0):
                raise Exception(
                    f"Sorry, Data Not Found for {query[0]} QP Code\nPlease Check QP Code and Try Again")
            dataString = ""
            for i, j in enumerate(data):
                if i == 0:
                    heading = f"<b><u>Time Table of QPCode {j['QPCode']}</u></b>\n\n\n"
                    dataString += heading
                singleData = f"🎓 University - <b>{j['University']}</b>\n📚 Course - <b>{j['Course']}</b>\n📖 Semester - <b>{j['Sem']}</b>\n📝 Subject Name - <b>{j['SubjectName']}</b>\n🗓️ Exam Date - <b>{j['Date']}</b>\n⏰ Exam Time - <b>{j['Time']}</b>\n❓ QP Code - <b>{j['QPCode']}</b>\n\n\n"
                dataString += singleData

            update.message.reply_html(dataString)
            update.message.reply_html(ht.footer, disable_web_page_preview=True)
        except Exception as e:
            print(str(e))
            update.message.reply_text("Something Went Wrong\nReport to Admin")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.

    updater = Updater(
        token=os.environ.get("BOT_TOKEN"), use_context=True)
    PORT = int(os.environ.get('PORT', '8443'))
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("contact", contactus))
    dispatcher.add_handler(CommandHandler("qpcode", getTimeTablefromQPCode))
    updater.dispatcher.add_handler(CallbackQueryHandler(callBackQuery))

    dispatcher.add_error_handler(error)
    # Start the Bot
    updater.start_webhook(listen="0.0.0.0", port=PORT,
                          url_path=os.environ.get("BOT_TOKEN"))
    updater.bot.set_webhook(
        os.environ.get("HOST_NAME") + os.environ.get("BOT_TOKEN"))
    logging.info("Starting Long Polling!")

    updater.idle()


if __name__ == '__main__':
    main()
