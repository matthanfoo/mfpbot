print('running teleadmin')
import logging
import datetime
import sqlite3
import re

import requests


from telegram import Update, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Bot
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, CallbackQueryHandler, JobQueue, CallbackContext, ConversationHandler
from tpfpostgre import *
from telepostgre import execute_pgsql
from queue import Queue
from telegram.ext import Updater

def estab_conn(db_name):
    conn = sqlite3.connect(f'{db_name}.db')
    return conn

telebot = Bot(token = "5811073358:AAGgEtuRoV4T1f4zKjukgu3-gTJpAqogru0")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "5811073358:AAGgEtuRoV4T1f4zKjukgu3-gTJpAqogru0"
chatid = '298000154'
application = ApplicationBuilder().token(TOKEN).build()


def send_to_admin(message='hello'):
    TOKEN = "5811073358:AAGgEtuRoV4T1f4zKjukgu3-gTJpAqogru0"
    chatid = '298000154'
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chatid}&text={message}"
    requests.get(url).json()



async def autolog(update: Update, context):

    try:
        print(update.callback_query.data)
        data = update.callback_query.data
    except:
        data = False

    time = datetime.datetime.now()
    if not data:

        print(context.args)
        if len(context.args)>0:
            date = context.args[0]
            print('date:', date)
            try:
                datedifferent = datetime.datetime.strptime(date, '%d-%m-%y')
                print('try',datedifferent)
            except:
                await context.bot.send_message(chat_id=update.effective_chat.id, text='invalid date')
                return False
        else:
            datedifferent = False
        context.user_data['datedifferent'] = datedifferent
    else:
        datedifferent = context.user_data['datedifferent']



    
    loggeddates = [date[0] for date in execute_pgsql('select date from logtracker',fetchall=True)]# find a list of all logged dates
    if not datedifferent:
        datedifferent = datetime.datetime.now()  # if no date provided with logshit call, put datedifferent as todays datetime
    testdatestring = datedifferent.strftime('%d-%m-%Y')
    if str(testdatestring) in loggeddates: #if macros have been logged before and its a first time call, tell admin
        if not data:
            keyboard = [[InlineKeyboardButton("log anyway", callback_data='log_anyway'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'macros already logged for {testdatestring}',reply_markup=reply_markup)
            return False
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'logging macros again for {testdatestring}')

    print(loggeddates)


    print('sending dd:', True, type(datedifferent))


    usernamelist = [usernametup[0] for usernametup in execute_pgsql('SELECT username FROM all_users',fetchall=True)]
    singleautologsuccess = False
    for username in usernamelist:
        try:
            print(f'log_macros for {username} started at {time}')
            send_to_admin(f'log_macros for {username} started at {time}') #send to admin to let them know log_macros started for which user
            log_macros(username, True, datedifferent)
            send_to_admin(f'autolog for {username} success at {time}') #send to admin to let them know log_macros success for which user
            singleautologsuccess = True
        except Exception as e:
            print(f'log_macros for {username} failed with exception {e}')
            send_to_admin(f'log_macros for {username} failed with exception {e}')

    if singleautologsuccess:
        x = execute_pgsql(f"SELECT logcount FROM logtracker WHERE date = '{testdatestring}'",fetchone=True)
        if x: #if logmacros has been called for data before
            execute_pgsql(f'UPDATE logtracker SET logcount = %s WHERE date = %s', (str(int(x[0])+1), testdatestring))
        else:
            execute_pgsql(f'INSERT INTO logtracker VALUES(%s,%s)', (testdatestring, '1'))
        print('final', execute_pgsql(f'SELECT * FROM logtracker WHERE date = \'{testdatestring}\'',fetchone=True))
    else:
        print('not a single autolog was successful')
    


async def cunt(update: Update, context: CallbackContext):
    message = "run that shit boi"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)



send_to_admin(f'tele.py running started at time: {datetime.datetime.now()}')
cunt_handler = CommandHandler('cunt', cunt)
log_handler = CommandHandler('logshit', autolog)
loganyway = CallbackQueryHandler(autolog, 'log_anyway')


application.add_handler(cunt_handler)
application.add_handler(log_handler)
application.add_handler(loganyway)
# application.add_handler(CallbackQueryHandler(testhandlerfunction))

print('polling teleadmin')
application.run_polling()
print('teleadmin ended')
send_to_admin('teleadmin ended')
