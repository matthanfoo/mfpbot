print('running')
import psycopg2
import logging
import datetime
import sqlite3
from time import sleep
import re
import schedule
import requests
##from dbcontrol import estab_conn
from telegram import Update, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from tpfpostgre import *
print('running2')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print(f'tele.py running started at time: {datetime.datetime.now()}')
application = ApplicationBuilder().token("5948121349:AAG3k_7Wv-aCxyQlJzCtR0U4vcN8-onmUqI").build()

def send_to_admin(message='hello'):
    TOKEN = "5811073358:AAGgEtuRoV4T1f4zKjukgu3-gTJpAqogru0"
    chatid = '298000154'
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chatid}&text={message}"
    requests.get(url).json()


def execute_pgsql(sql: str, values=[], fetchall=False, fetchone=False, fetchmany=False):

    #SETUP
    #SET TOKEN AS MFPNEWBOT TOKEN
    API_TOKEN = "5948121349:AAF_BtTRt0ckuYnZbDO81pv7aOVpZAT4aVs""5948121349:AAF_BtTRt0ckuYnZbDO81pv7aOVpZAT4aVs"
    #SET DB URL FROM RAILWAY
    DB_URL = "postgresql://postgres:ZvoYvy6Lp78aZm2MBk5p@containers-us-west-155.railway.app:7864/railway"
   
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()

    result = False
    #TRY BLOCK
    try:
        if fetchall:
            if len(values)==0:
                print('fetchall, lv=0')
                cur.execute(sql)
                try:
                    result = cur.fetchall()
                except:
                    pass
            else:
                print('fetchall, lv=+')
                resultpre = cur.execute(sql, values)
                try:
                    result = cur.fetchall()
                except:
                    pass
        elif fetchone: 
            if len(values)==0:
                print('fetchone, lv=0')
                resultpre = cur.execute(sql)
                try:
                    result = cur.fetchone()
                except:
                    pass
            else:
                print('fetchone, lv=+')
                resultpre = cur.execute(sql, values)
                try:
                    result = cur.fetchone()
                except:
                    pass
        elif fetchmany:
            if len(values)==0:
                print('fetchmany, lv=0')
                resultpre = cur.execute(sql)
                try:
                    result = cur.fetchmany()
                except:
                    pass
            else:
                print('fetchmany, lv=+')
                resultpre = cur.execute(sql, values)
                try:
                    result = cur.fetchmany()
                except:
                    pass
        else:
            if len(values)==0:
                print('nofetchall, lv=0')
                result = cur.execute(sql)

            else:
                print('nofetchall, lv=+')
                result = cur.execute(sql, values)
        conn.commit()
        
        print(f'successful execution of pgsql: result: {result}, sql: \'{sql}\'')
    except Exception as e:
        print(f'pgsql fail with exception {e}, sql: {sql}')
        result = e 
    
    cur.close()
    conn.close()
    return result
    

#verify if account created -- called by all functions except start and username -- returns username if userid exists and False if not
#by default sends msg to user if account does not exist, but prin False prevents the send
def verify_if_account_exists(userid, context, prin = True, update=''):
    '''checks if userid is in database, if not ask to create username'''
    if not userid_exists(userid):
        return False
    else:
        return userid_exists(userid)


#start function -- called by /start - welcomes user to bot and requests them to type username to create account - might need to have login function
async def start(update: Update, context):
    user = update.message.from_user
    print('user {}, user ID: {}, called /start'.format(user['username'], user['id']))

    if userid_exists(user['id']): #if id exists in userdatadb already, welcome back
        await context.bot.send_message(chat_id=update.effective_chat.id, text='welcome back, {}! \n\ntype /help to view available commands and options'.format(userid_exists(user['id'])))
    else: #if id exists in userdatadb already, welcome and direct to account creation (username)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="welcome to mfp_bot!")
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /username <your username> to create an account \n\nlike this: /username user1.')

#help function -- called at anytime - prints list of functions and commands
async def telehelp(update: Update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='''here is what you can do in mfpbot
\U0001F4CB /viewlog: your daily activity log
\U0001F4CA /viewmacros: your daily macro info
\U0001F3CB /viewgym: your gym PBs
\U0001F371 /newactivity: add activities to daily log \n'''+
u'\u2696' + ''' /updateweight update your weight
\U0001F4B8 /viewmoney: your food expenditure
\U0001F4D2 /customentry: add custom entries to personal database''')


#username function -- called by /username - if input is formatted correctly, verify username is unique, create user table in userdata.db, inform user
async def username(update: Update, context, tele_call=True):
    user = update.message.from_user

    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /username <your username> to create a username. \n\nlike this: /username user1.')
    else:
        print('user ID: {}, called /username'.format(user['id']))
        usernameinput = context.args[0].lower()
        if username_validation(usernameinput, user['id']):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'user {usernameinput} created. \n\ntype /setmacros to set your macro targets or /changeusername to change your username')
            send_to_admin(f'user {usernameinput} created')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'username {usernameinput} is already taken. \n\ntype /username <your username> to create another username \n\nlike this: /username user1')


#can be called by all users, introduces setbcg to new users and prints menu for existing users
async def setmacros(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /setmacros'.format(user['id']))
    if verify_if_account_exists(user['id'], context):
        keyboard = [[InlineKeyboardButton("macro calculator", url = 'https://www.fatcalc.com/bwp'),]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if usermacros_created(user['id']):
            # await context.bot.send_message(chat_id=update.effective_chat.id, text='find out more about your daily macro targets at: \n\nhttps://www.fatcalc.com/bwp \n', disable_web_page_preview=True)
            await context.bot.send_message(chat_id=update.effective_chat.id, text='''which targets would you like to set? \n
bcg - /setbcg <your bcg>
protein - /setp <your protein target>
carbs - /setc <your carb target>
fat - /setf <your fat target>
weight - /setw <your weight goal>
current weight - /updateweight <your current weight>

or type /help to view available commands and options''', reply_markup=reply_markup)
        else:
            await update.message.reply_text(text='calculate your daily macro targets', reply_markup=reply_markup)
            # await context.bot.send_message(chat_id=update.effective_chat.id, text='find out more about your daily macro targets at: \n\nhttps://www.fatcalc.com/bwp \n', disable_web_page_preview=True)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=
            '''let's start with your base calorie goal.
            
base calorie goal (bcg) - a specific amount of calories that you aim to consume on a daily basis in order to reach your weight goal.
            
type /setbcg <your bcg> to set bcg.
            
like this: /setbcg 2000''')

    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


#can be called by any user, when called (verifies input is integer then updates default in database) (introduce setp function to set protein goal)
async def setbcg(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /setbcg'.format(user['id']))

    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /setbcg <your bcg> to set bcg. \n\nlike this: /setbcg 2000')
    try:
        value = int(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<your bcg> must be a number')
    else:
        if verify_if_account_exists(user['id'], context):
            set_macro = sql_set_defaultmacro('calout', value, user['id'])
            if set_macro == 'true': #successful set of default macro - tell user success and redirect to other functions
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'your daily bcg has been set to {value} calories')
                await context.bot.send_message(chat_id=update.effective_chat.id, text ='type /setmacros to set your other macro targets or /setbcg <new bcg> to change your bcg' )
            else: #unsuccessful set of default macro -- tell user got issue and tell admin got issue
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'there was an issue setting this value\ntry using /setbcg again or contact bot admin at @xxx')
                send_to_admin(f'set bcg fail for user {username} with exception {set_macro[1]}')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


async def setp(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /setp'.format(user['id']))

    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /setp <your protein target> to set your protein target in grams. \n\nlike this: /setp 120')
    try:
        value = int(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<your protein target> must be a number')
    else:
        if verify_if_account_exists(user['id'], context):
            set_macro = sql_set_defaultmacro('prottarget', value, user['id'])
            if set_macro == 'true': #successful set of default macro - tell user success and redirect to other functions
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'your daily protein target has been set to {value}g')
                await context.bot.send_message(chat_id=update.effective_chat.id, text ='type /setmacros to set your other macro targets or /setp <new protein target> to change your protein target')
            else: #unsuccessful set of default macro -- tell user got issue and tell admin got issue
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'there was an issue setting this value\ntry using /setp again or contact bot admin at @xxx')
                send_to_admin(f'set p fail for user {username} with exception {set_macro[1]}')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


async def setc(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /setc'.format(user['id']))
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /setc <your carb target> to set your carb target in grams. \n\nlike this: /setp 200')
    try:
        value = int(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<your carb target> must be a number')
    else:
        if verify_if_account_exists(user['id'], context):
            set_macro = sql_set_defaultmacro('carbtarget', value, user['id'])
            if set_macro == 'true': #successful set of default macro - tell user success and redirect to other functions
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'your daily carb target has been set to {value}g')
                await context.bot.send_message(chat_id=update.effective_chat.id, text ='type /setmacros to set your other macro targets or /setc <new carb target> to change your carb target' )
            else: #unsuccessful set of default macro -- tell user got issue and tell admin got issue
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'there was an issue setting this value\ntry using /setc again or contact bot admin at @xxx')
                send_to_admin(f'set c fail for user {username} with exception {set_macro[1]}')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


async def setf(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /setf'.format(user['id']))

    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /setf <your fat target> to set your fat target in grams. \n\nlike this: /setf 60')
    try:
        value = int(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<your fat target> must be a number')
    else:
        if verify_if_account_exists(user['id'], context):
            set_macro = sql_set_defaultmacro('fattarget', value, user['id'])
            if set_macro == 'true': #successful set of default macro - tell user success and redirect to other functions
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'your daily fat target has been set to {value}g')
                await context.bot.send_message(chat_id=update.effective_chat.id, text ='type /setmacros to set your other macro targets or /setf <new fat target> to change your fat target' )
            else: #unsuccessful set of default macro -- tell user got issue and tell admin got issue
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'there was an issue setting this value\ntry using /setf again or contact bot admin at @xxx')
                send_to_admin(f'set f fail for user {username} with exception {set_macro[1]}')

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')

async def setw(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /setw'.format(user['id']))
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /setw <your weight goal> to set your weight goal in kg. \n\nlike this: /setw 60')
    try:
        value = int(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<your weight goal> must be a number (can be a decimal)')
    else:
        if verify_if_account_exists(user['id'], context):
            set_macro = sql_set_defaultmacro('fattarget', value, user['id'])
            if set_macro == 'true': #successful set of default macro - tell user success and redirect to other functions
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'your weight goal has been set to {value}kg')
                await context.bot.send_message(chat_id=update.effective_chat.id, text ='type /updateweight <your current weight> to set your current weight or type /setmacros to set your other macro targets' )
            else: #unsuccessful set of default macro -- tell user got issue and tell admin got issue
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'there was an issue setting this value\ntry using /setw again or contact bot admin at @xxx')
                send_to_admin(f'set w fail for user {username} with exception {set_macro[1]}')

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')

async def updateweight(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /updateweight'.format(user['id']))
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='type /updateweight <your current weight> to update your current weight in kg. \n\nlike this: /updateweight 60')
    try:
        value = float(context.args[0])
    except:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='<your weight> must be a number (can be a decimal)')
    else:
        username = verify_if_account_exists(user['id'], context)
        if username:
            datetoday = datetime.datetime.now().strftime("%d-%m-%Y")
            print(datetoday)
            
            presql = f'DELETE FROM tracking_{username} where date LIKE \'%{datetoday}%\''
            x= False
            try:
                execute_pgsql(presql) #IF WEIGHT FOR TODAY INPUTTED BEFORE THEN DELETE
                execute_pgsql(f'INSERT INTO tracking_{username}(date,weight) VALUES(%s,%s)', (datetoday, value))
                conn.commit()
                conn.close()
                x = True
            except Exception as e:
                print(e)
            if x: #successful set of weight
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'your weight has been updated to {value}kg')
                await context.bot.send_message(chat_id=update.effective_chat.id, text ='type /help to view other functions' )
            else: #unsuccessful set of default macro -- tell user got issue and tell admin got issue
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f'there was an issue setting this value\ntry using /updateweight again or contact bot admin at @xxx')
                send_to_admin(f'updateweight fail for user {username} with exception {e}')

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


async def viewlog(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /viewlog'.format(user['id']))
    username = verify_if_account_exists(user['id'], context)
    if not username: #if username does not exist, v_i_a_e will tell user they have nt created account and return False
        await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')
        return False #end viewlog function
    else:
        pass #continue viewlog function

    printstring = display_activity_log(username, True) #return a formatted activity log print string
    printstring += '\n\ntype /newentry to add a new activity'
    if printstring != 'no activities today :/':
        printstring += '\n type /viewmacros to view today\'s macros'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=printstring)


async def viewmacros(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /viewmacros'.format(user['id']))
    username = verify_if_account_exists(user['id'], context, update=update)
    if not username: #if username does not exist, v_i_a_e will tell user they have nt created account and return False
        await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')
        return False #end viewmacros function
    else:
        pass #continue viewmacros function

    try:
        printstring = display_macros(username)
    except Exception as e:
        send_to_admin(f'display_macros called by {username} and failed with exception {e}')
    else:
        printstring += '\n\ntype /newentry to add a new activity'
        printstring += '\n type /setmacros to change your macro goals'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=printstring)
        print(f'display_macros called by {username} and returned the formatted printstring correctly')


async def viewgympri(update: Update, context):
    user = update.message.from_user
    print('user ID: {}, called /viewgym'.format(user['id']))
    username = verify_if_account_exists(user['id'], context, update=update)
    if not username: #if username does not exist, v_i_a_e will tell user they have nt created account and return False
        return False #end viewgym function
    else:
        pass #continue viewgym function

    buttons = [[
        InlineKeyboardButton(text="biceps", callback_data='biceps'),
        InlineKeyboardButton(text="triceps", callback_data='triceps'),
        InlineKeyboardButton(text="shoulders", callback_data='shoulders')],
        [
        InlineKeyboardButton(text="back", callback_data='back'),
        InlineKeyboardButton(text="chest", callback_data='chest'),
        InlineKeyboardButton(text="abs", callback_data='abs'),
        InlineKeyboardButton(text="legs", callback_data='legs')]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text('select muscle group:', reply_markup=keyboard)


async def viewgymhandle(update: Update, context):
    user = update.callback_query.from_user
    username = verify_if_account_exists(user['id'], context)

    query = update.callback_query
    group = query.data
    print(group)
    await query.answer()

  
    #get all gym records for specified group - search for entries with names that contain <group> AND lift (incase like meals got core inside also)
    names = execute_pgsql(f'SELECT * FROM uniquedata_{username} WHERE name LIKE \'%lift%\' AND name LIKE \'%{group}%\'',fetchall=True)
    lifts_string = f'''current PBs for {group}
------------------------\n'''
    print('here')
    for i in names: #compile print string for display to user
        lift, groupname, exname = i[1].split(", ")
        sets = int(i[2])
        weight = float(i[3])
        reps = int(i[4])
        if sets == 0 and weight == 0 and reps == 0:
            pass
        else:
            lifts_string += f'{groupname}, {exname}: {str(sets)}x{str(reps)} {weight} kg\n'
    if lifts_string == f'''current PBs for {group}\n------------------------\n''':
        lifts_string = f'no current PBs for {group}'
    lifts_string += '\ntype /viewgym again to view PBs for another muscle group'

    await context.bot.send_message(chat_id=update.effective_chat.id, text=lifts_string)
    print('here3')
    print(f'viewgym called by {username} and returned the formatted lifts_string correctly')
    ####TEST THIS FUNCTION TO SEE IF BUTTONS REMAIN AFTER SELECTION IF SO THEN DONT NEED TO REDIRECT TO VIEWGYM AGAIN


async def unknown(update: Update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


async def testfunction(update, context):
    keyboard = [[InlineKeyboardButton("toxic", callback_data='toxicabc123'), InlineKeyboardButton("nottoxic", callback_data='nottoxicabc123') ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id = update.effective_chat.id, text='dog', reply_markup=reply_markup)

async def testhandlerfunction(update, context: CallbackContext):

    query = update.callback_query
    # print(query.data)


#echo function -- no use yet
async def echo(update: Update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)







####################################CONV HANDLER############################################

# State definitions for states (initial states before split for gym
SELECTING_SUBTYPE, TYPING_STRING, SEARCH_NEW_NAME, SELECTING_OPTION, SELECT_DIFF_OPTION, TYPING_QU4NTITY, CHANGE_QUANTITY = map(chr, range(7))
# State definitions for states (states for gym numbers)
SELECTING_REPLACE, TYPING_SETS, TYPING_WEIGHT, CHANGE_WEIGHT, TYPING_REPS, CHANGE_REPS = map(chr,range(7, 13))
# State definitions for states (datetime)
SELECTING_DATE, CHANGE_DATE, TYPING_TIME, CHANGE_TIME = map(chr,range(13, 17))
# State definitions for states (completing entries)
COST_YESNO, TYPING_COST, CHANGE_COST, VERIFYING_RESTART, CONFIRMING_RESTART, NEWORADD, CONFIRMING_REPS, CONFIRMING_WEIGHT = map(chr,range(17, 25))
SINGLE_ENTRY, GYM_ADDORSAVE, TYPING_TYTLE, FOOD_ADDORSAVE, INVALID_SEARCH, INVALID_OPTION, CONFIRMING_TIME = map(chr,range(25, 32))
END = ConversationHandler.END
print('XXXXXXX', TYPING_TYTLE == TYPING_STRING)
print(type(SELECTING_SUBTYPE), type(TYPING_STRING), type(SELECTING_OPTION), type(END), sep='\n')
async def newactivity(update: Update, context):
    try:
        query = update.callback_query #check for callback query
        data = query.data
        print('ne have cbquery')
        if data == 'reselect_subtype': #if there is callbackquery data, it means its a backwards call, so just display the buttons again for user to click
            user = update.callback_query.from_user
            print('user ID: {}, called /newactivity'.format(user['username']))

            title = context.user_data['activitytitle']
        print('hertry3')
        buttons = [
            [
                InlineKeyboardButton(text="breakfast", callback_data='breakfast'),
                InlineKeyboardButton(text="snack", callback_data='snack'),
            ],
            [
                InlineKeyboardButton(text="lunch", callback_data='lunch'),
                InlineKeyboardButton(text="dinner", callback_data='dinner'),
            ],
            [
                InlineKeyboardButton(text="cardio", callback_data='cardio'),
                InlineKeyboardButton(text="sport", callback_data='sport'),
                InlineKeyboardButton(text="gym", callback_data='gym'),
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text='select activity type', reply_markup=keyboard) #ask user to click button to select activity type
        return SELECTING_SUBTYPE
    except: #normal call and not reverse callback from reverse
        print('ne fwd call')
        user = update.message.from_user
        print('user ID: {}, called /newentry'.format(user['username']))
        if verify_if_account_exists(user['id'], context):
        #     if title == 'x': #if activitytitle provided with command is x, save title as empty string
        #         context.user_data['activitytitle'] = ''
        # else:
        #     context.user_data['activitytitle'] = title #save title as title provided

            buttons = [
                [
                    InlineKeyboardButton(text="breakfast", callback_data='breakfast'),
                    InlineKeyboardButton(text="snack", callback_data='snack'),
                ],
                [
                    InlineKeyboardButton(text="lunch", callback_data='lunch'),
                    InlineKeyboardButton(text="dinner", callback_data='dinner'),
                ],
                [
                    InlineKeyboardButton(text="cardio", callback_data='cardio'),
                    InlineKeyboardButton(text="sport", callback_data='sport'),
                    InlineKeyboardButton(text="gym", callback_data='gym'),
                ],
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            await update.message.reply_text(text='select activity type     ', reply_markup=keyboard) #ask user to click button to select activity type
            return SELECTING_SUBTYPE
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


async def req_for_title(update: Update, context):
    print(conv_handler.check_update(update))
    subtype = update.callback_query.data
    if subtype in ['breakfast', 'lunch', 'dinner', 'snack']:
        maintype = 'food'
    else:
        maintype = 'workout'
    context.user_data['maintype'] = maintype #save type in user data
    context.user_data['subtype'] = subtype #save subtype in user data

    subtype_string = subtype if maintype == 'food' else str(subtype + ' activity')
    message = f'enter a title for your {subtype_string}\n\nor click \U0001F447 to skip title'
    keyboard = [[InlineKeyboardButton("skip title", callback_data='skip_title'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=message, reply_markup=reply_markup)
    print('returning typing_tYtle')
    return TYPING_TYTLE

async def req_for_search(update: Update, context):
    print('in rfs')
    subtype = context.user_data['subtype']
    maintype = context.user_data['maintype']
    try:
        title = update.message.text #forward call with title text
        context.user_data['activitytitle'] = title
    except:
        # print(update.callback_query.data)
        if update.callback_query.data == 'skip_title': #forward call with skip title
            # print('true')
            context.user_data['activitytitle'] = subtype
        else: #reverse call
            # print('frue')
            title = context.user_data['activitytitle']

    if maintype == 'food' or subtype == 'gym':
        try:
            print(context.user_data['tempdict'])
            if len(context.user_data['tempdict']) < 1:
                context.user_data['tempdict'] = [] #if no entries in dictionary, reinitialise jic
        except:
            context.user_data['tempdict'] = [] #initialise if tempdict does not exist

    a = 'food' if maintype == 'food' else 'lift' if subtype == 'gym' else subtype
    message = f'type to search for a {a} \nor click \U0001F447 to select a different activity type'
    keyboard = [[InlineKeyboardButton("select different activity type", callback_data='reselect_subtype'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(text=message, reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=message, reply_markup=reply_markup)

    print('returning typing_string')
    return TYPING_STRING

async def select_option(update: Update, context):
    print('s_o')
    maintype = context.user_data['maintype']
    subtype = context.user_data['subtype']
    title = context.user_data['activitytitle']

    try:
        searchname = update.message.text
        context.user_data['searchname'] = searchname
        #if update.message text exists, select_option call is from message handler (forward call from r_f_s), save searchname as update.message.text
    except Exception:
        print('here4')
        searchname = context.user_data['searchname']
        #if update.message.text does not exists, s_o call is from cqh (reverse call from r_f_q), retrieve originally searched searchname
    try:
        user = update.message.from_user
    except:
        user = update.callback_query.from_user
    userid = user['id'] #get username from userid
    username = verify_if_account_exists(userid, context, prin=False) #get username from viae and prevents message send

    a = 'food' if maintype == 'food' else 'lift' if subtype == 'gym' else subtype

    message = f'searching {a} database for: {searchname}...'
    try:
        await update.message.reply_text(message)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message)
    

    print(f'searchname: {searchname}')
    splitsearchname = searchname.split(' ')
    sql1 = ''
    if len(splitsearchname) == 1:
        sql1 = f'SELECT * FROM uniquedata_{username} WHERE name LIKE \'%{a}%\' AND name LIKE \'%{searchname}%\''
    elif len(splitsearchname) == 2:
        sql1 = f'SELECT * FROM uniquedata_{username} WHERE name LIKE \'%{a}%\' AND name LIKE \'%{splitsearchname[0]}%\' AND name LIKE \'%{splitsearchname[1]}%\''
    elif len(splitsearchname) == 3:
        sql1 = f'SELECT * FROM uniquedata_{username} WHERE name LIKE \'%{a}%\' AND name LIKE \'%{splitsearchname[0]}%\' AND name LIKE \'%{splitsearchname[1]}%\' AND name LIKE \'%{splitsearchname[2]}%\''
    elif len(splitsearchname) > 3:
        x = ' '.join(splitsearchname[2:])
        sql1 = f'SELECT * FROM uniquedata_{username} WHERE name LIKE \'%{a}%\' AND name LIKE \'%{splitsearchname[0]}%\' AND name LIKE \'%{splitsearchname[1]}%\' AND name LIKE \'%{x}%\''
    print(sql1)
    try:
        results = execute_pgsql(sql1,fetchall=True)
        if len(results) < 1:
            message2 = f'no {a} found containing {searchname}\n\nclick \U0001F447 to search for another {a}\n\nor type /exit then /customentry to create a new {a}'
            keyboard = [[InlineKeyboardButton(f"search for another {a}", callback_data=subtype),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await update.message.reply_text(text=message2, reply_markup=reply_markup)
            except:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text=message2, reply_markup=reply_markup)
            return SELECTING_OPTION
        else:
            internaldict = {}
            message2 = f'search results for {searchname}: \n'
            for searchid in range(1, len(results)+1):
                internaldict[searchid] = results[searchid-1] #tag each result with a search id
            for searchid, val in internaldict.items():
                itemname = ', '.join(val[1].split(', ')[1:])
                msgpart = f'{searchid}: {itemname}\n' #print search id: item name
                message2 += msgpart
            context.user_data['resultsdict'] = internaldict #save internaldict to userdata for next function to access
            print(internaldict, 'so')
            message2 += f'\ntype the number of the {a} you would like to add to the actvity \n\nor click \U0001F447 to search for another {a}'
    except:
        message2 = f'no {a} found containing {searchname}\n\nclick \U0001F447 to search for another {a}'

    keyboard = [[InlineKeyboardButton(f"search for another {a}", callback_data=subtype),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(text=message2, reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=message2, reply_markup=reply_markup)
    return SELECTING_OPTION

async def req_for_quantity(update: Update, context):
    print('rfq')
    maintype = context.user_data['maintype']
    subtype = context.user_data['subtype']
    title = context.user_data['activitytitle']
    resultsdict = context.user_data['resultsdict']
    print(resultsdict, 'rfq')
    try:
        #if update.message.text is available, means forward call and save the selectedoption
        selectedoption = int(update.message.text)
        searchid = str(resultsdict[selectedoption][0]) # get the database id of selected entry from user
        context.user_data['selectedoption'] = selectedoption
        context.user_data['searchid'] = searchid # save the database id of selected entry to user_data
        print('successful option select')
    except Exception as e:
        print(e)
        if e == ValueError:
            keyboard = [[InlineKeyboardButton(text="select different option", callback_data='sdo'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text='invalid option\n\nclick \U0001F447 to re-select option', reply_markup=reply_markup)
            return INVALID_OPTION #if invalid input and cannot find in resultsdict, revert by using INVALID_OPTION state to handle callbackquery sdo

        #if update.message.text is unavailable, means either backward or invalid call
        try:
            #if context.user_data['selectoption' is available, it means its a callback where so and si have been saved before
            selectedoption = context.user_data['selectedoption']
            searchid = context.user_data['searchid']
            print('successful reverse to selectoption')
        except:
            #handles case where selected option is not inside resultsdict or if selected option is invalid
            keyboard = [[InlineKeyboardButton(text="select different option", callback_data='sdo'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text='invalid option\n\nclick \U0001F447 to re-select option', reply_markup=reply_markup)
            return INVALID_OPTION #if invalid input and cannot find in resultsdict, revert by using INVALID_OPTION state to handle callbackquery sdo



    print(resultsdict[selectedoption])
    a = 'food' if maintype == 'food' else 'lift' if subtype == 'gym' else subtype
    itemname = ', '.join(resultsdict[selectedoption][1].split(', ')[1:]) #split name string by entry and remove the type from name to recreate string without type
    context.user_data['itemname'] = itemname
    if a == 'food':
        def get_mac_from_desc(description):
            print(f'getting mac from {description}')
            def get_p_from_desc(description):
                p_pattern = 'P:.+g, F'
                p_pattern2 = 'P:.+g,'
                p_pattern3 = '\d.+\d'
                match = re.search(p_pattern, description).group()
                match2 = re.search(p_pattern2, match).group()
                match3 = re.search(p_pattern3, match2).group()
                return float(match3)

            def get_c_from_desc(description):
                c_pattern = 'C:.+g, P'
                c_pattern2 = '\d.+\d'
                match = re.search(c_pattern, description).group()
                match2 = re.search(c_pattern2, match).group()
                # print(match2)
                return float(match2)

            def get_f_from_desc(description):
                f_pattern = 'F:.+g'
                f_pattern2 = '\d.+\d'
                match = re.search(f_pattern, description).group()
                match2 = re.search(f_pattern2, match).group()
                # print(match2)
                return float(match2)

            p = get_p_from_desc(description)
            c = get_c_from_desc(description)
            f = get_f_from_desc(description)
            return c, p, f
        servingsize = str(float(resultsdict[selectedoption][2]))
        servingsizeunit = str(resultsdict[selectedoption][3])
        context.user_data['ssvalue'] = servingsize
        context.user_data['ssunit'] = servingsizeunit
        cal = str(int(resultsdict[selectedoption][4]))
        c, p, f = tuple([str(x) for x in get_mac_from_desc(resultsdict[selectedoption][5])])
        context.user_data['cal'] = cal
        context.user_data['cpf'] = ', '.join([c, p, f])
        selected_message = f'you have selected {itemname}\n1 serving: {servingsize} {servingsizeunit}\n{cal} cal, c: {c}g, p: {p}g, f: {f}g'
        rfq_message = f'enter servings \nor click \U0001F447 to select another option'
    elif a == 'cardio' or a == 'sport':
        mets = float(resultsdict[selectedoption][4])
        user = update.message.from_user
        username = verify_if_account_exists(user['id'], context, prin=False) #get username from viae and prevents message send
        
        sql2 = f'SELECT date FROM tracking_{username}'
        dates = [x[0] for x in execute_pgsql(sql2, fetchall=True)]
        try:
            dates.remove('default')
        except:
            pass
        #find latest date
        datetimes = []
        for dead in dates:
            dt = datetime.datetime.strptime(dead_string, "%d-%m-%Y")
            datetimes.append(dt)

        latestdateobject = max(datetimes)
        latestdatestring = latestdateobject.strftime("%d-%m-%Y")

        sql3 = f"SELECT weight from tracking_{username} WHERE date = '{latestdatestring}'"
        weightpre = execute_pgsql(sql3, fetchone=True)
        weight = float(weightpre[0]) if len(weightpre)==0 else 60.0
        calsperhr = round(mets * float(weight) * 3.5 * 60 / 200)
        selected_message = f'you have selected {itemname}\n60 mins, {calsperhr} cal'
        context.user_data['cph'] = calsperhr
        rfq_message = f'enter minutes of activity \nor click \U0001F447 to select another option'
    elif a == 'lift':
        sets = int(resultsdict[selectedoption][2])
        if sets == 0.0: #check if sets have been set before (if not, it is untouched from basedata, if is, pb has been set before)
            req_for_sets = f'enter the number of sets for {itemname} \n\nor click \U0001F447 to select another lift'
            context.user_data['pb'] = 'false'
            keyboard = [[InlineKeyboardButton(text="select different lift", callback_data='sdo'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                await update.message.reply_text(text=req_for_sets, reply_markup=reply_markup)
            except:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text=req_for_sets, reply_markup=reply_markup)
            return TYPING_SETS
        else:
            weight = str(float(resultsdict[selectedoption][3]))
            reps = str(int(resultsdict[selectedoption][4]))
            pb_string = f'you have set a pb for {itemname} before: \nsets: {sets}, weight: {weight}kg, reps: {reps}'
            context.user_data['pb'] = 'true'
            rfr_message = f'would you like to set a new pb?'
            buttons = [
                [
                    InlineKeyboardButton(text="yes", callback_data='yes'),
                    InlineKeyboardButton(text="no", callback_data='no'),
                ],
                [
                    InlineKeyboardButton(text="select different lift", callback_data='sdo'),
                ],
            ]
            keyboard = InlineKeyboardMarkup(buttons)

            try:
                await update.message.reply_text(text=pb_string)
                await update.message.reply_text(text=rfr_message, reply_markup=keyboard)
            except:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text=pb_string)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=rfr_message, reply_markup=keyboard)
            return SELECTING_REPLACE

    keyboard = [[InlineKeyboardButton(f"select another option", callback_data='sdo'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(selected_message)
        await update.message.reply_text(rfq_message, reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=selected_message)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=rfq_message, reply_markup=keyboard)
    x = TYPING_QU4NTITY
    print(f'returning {x}')
    return x

async def temp_yesno_replace(update: Update, context):
    print(update.callback_query.data)
    itemname = context.user_data['itemname']
    if update.callback_query.data == 'yes':
        context.user_data['replace'] = 'true'
        notstr = ' '
    else:
        notstr = ' not '
        context.user_data['replace'] = 'false'
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(f'you have selected{notstr}to replace pb for {itemname}')
    req_for_sets = f'enter the number of sets for {itemname}\n\nor click \U0001F447 to select another lift'

    keyboard = [[InlineKeyboardButton(text="select different lift", callback_data='sdo'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id,text=req_for_sets, reply_markup=reply_markup)
    return TYPING_SETS

async def req_for_reps(update: Update, context):
    try:
        sets = int(update.message.text) #try to get sets input (text)
    except:
        try:
            sets = context.user_data['sets'] #if sets has been set before i.e. backwards call from rfr:
        except:
            keyboard = [[InlineKeyboardButton(text="change sets", callback_data='cq'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text='invalid input\n\nclick \U0001F447 to re-enter sets', reply_markup=reply_markup)
            return CHANGE_QUANTITY #if invalid input and cannot find sets, revert

    context.user_data['sets'] = sets #save sets for future reference
    itemname = context.user_data['itemname']
    req_for_reps = f'enter reps per set for {itemname}, {sets} sets\n\nor click \U0001F447 to re-enter sets'
    keyboard = [[InlineKeyboardButton(text="change sets", callback_data='cq'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(text=req_for_reps, reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=req_for_reps, reply_markup=reply_markup)

    return TYPING_REPS

async def req_for_weight(update: Update, context):
    print(update.message.text)
    try:
        reps = int(update.message.text) #try to get reps input (from text message)
    except:
        try:
            reps = context.user_data['reps'] #if reps have been set before i.e. backwards call from verify_weight:
        except:
            keyboard = [[InlineKeyboardButton(text="change reps", callback_data='cr'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text='invalid input\n\nclick \U0001F447 to re-enter sets', reply_markup=reply_markup)
            return TYPING_WEIGHT #if invalid input and cannot find reps, revert

    context.user_data['reps'] = reps #save reps for future reference
    itemname = context.user_data['itemname']
    sets = context.user_data['sets']
    req_for_reps = f'enter weight (kg) for\n{itemname}, {sets} sets x {reps} reps\n\nor click \U0001F447 to re-enter sets'
    keyboard = [[InlineKeyboardButton(text="change reps", callback_data='cr'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(text=req_for_reps, reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=req_for_weight, reply_markup=reply_markup)
    return TYPING_WEIGHT

async def verify_weight(update: Update, context):
    print('verify_weight', update.message.text)
    try:
        weight = float(update.message.text) #try to get weight input (from text message)
    except:
        keyboard = [[InlineKeyboardButton(text="change weight", callback_data='cw'),]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text='invalid input\n\nclick \U0001F447 to re-enter weight', reply_markup=reply_markup)
        return CONFIRMING_WEIGHT #if invalid input and cannot find weight, revert to rfw

    context.user_data['weight'] = weight #save weight for future reference
    # itemname = context.user_data['itemname']
    # sets = context.user_data['sets']
    # weight = context.user_data['weight']
    # liftstring = f'lift: {itemname}, {weight} kg x {sets} sets\n\n\nor click \U0001F447 to re-enter sets'
    # req_for_date = f'enter reps for\n{itemname}, {weight} kg x {sets} sets\n\n\nor click \U0001F447 to re-enter sets'
    keyboard = [[InlineKeyboardButton(text="confirm", callback_data='yes'), InlineKeyboardButton(text="change weight", callback_data='cw'), ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_text(text=f'confirm weight: {weight} kg', reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=f'confirm weight: {weight} kg', reply_markup=reply_markup)
    return CONFIRMING_WEIGHT

async def process_lift(update:Update, context):
    print('process_lift')
    itemname = context.user_data['itemname']
    searchid = context.user_data['searchid']
    sets = context.user_data['sets']
    weight = context.user_data['weight']
    reps = context.user_data['reps']
    title = context.user_data['activitytitle'] #persist
    tempdict = context.user_data['tempdict'] #persist
    pb = context.user_data['pb']
    try:
        replace = context.user_data['replace']
    except:
        replace = 'false'
    print(itemname, sets, weight, reps, title, tempdict)
    appendstring = '|'.join((str(searchid),str(itemname),str(sets),str(reps),str(weight),str(pb),str(replace))) #format a string to append to temp dict
    print(appendstring)
    tempdict.append(appendstring)
    context.user_data['tempdict'] = tempdict #rewrite temp dict
    shorteneditemname = ', '.join(itemname.split(', ')[:-1])
    printstring = f'''{shorteneditemname}: {str(sets)}x{str(reps)} {weight} kg
{shorteneditemname} added to {title}'''
    req_for_save = f'would you like to add another lift to {title}?'

    keyboard = [[InlineKeyboardButton(text="add another lift", callback_data='gym'),],
                [InlineKeyboardButton(text=f"done, save workout to activity log", callback_data='save'), ],]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=printstring)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=req_for_save, reply_markup=reply_markup)
    return GYM_ADDORSAVE

async def process_quantity(update:Update, context):
    try:
        quantity = float(update.message.text)
        context.user_data['quantity'] = quantity
    except:
        keyboard = [[InlineKeyboardButton(text="change quantity", callback_data='cq'),]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text='invalid input\n\nclick \U0001F447 to re-enter quantity', reply_markup=reply_markup)
        return SINGLE_ENTRY #if invalid input and cannot find weight, revert to rfq

    maintype = context.user_data['maintype']
    subtype = context.user_data['subtype']
    itemname = context.user_data['itemname']
    print(maintype)
    if maintype == 'food':
        try:
            ssunit = context.user_data['ssunit']
            ssvalue = context.user_data['ssvalue']
        except Exception as e:
            print(e)
            await update.message.reply_text(text='error')
            return END
        ssvalue = float(context.user_data['ssvalue'])
        calsperserving = float(context.user_data['cal'])
        cps, pps, fps = [float(x) for x in context.user_data['cpf'].split(', ')]
        cals = round(calsperserving * quantity)
        c = round(cps * quantity)
        p = round(pps * quantity)
        f = round(fps * quantity)
        #save calculated cals, cpf, for given quantity
        context.user_data['calquan'] = cals
        context.user_data['cpfquan'] = '|'.join([str(c), str(p), str(f)])

        keyboard = [[InlineKeyboardButton(text="yes", callback_data='yes'), InlineKeyboardButton(text="no", callback_data='no'), ],
                    [InlineKeyboardButton(text="enter different quantity", callback_data='cq'),],]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text=f'quantity: {quantity} {ssunit}')
        await update.message.reply_text(text=f'would you like to input a cost for {itemname}, {quantity} {ssunit}', reply_markup=reply_markup)
        return COST_YESNO
    elif subtype == 'cardio' or subtype == 'sport':
        searchid = int(context.user_data['searchid'])
        title = context.user_data['activitytitle'] #persist
        cph = context.user_data['cph']
        # user = update.message.from_user
        # username = verify_if_account_exists(user['id'], context, prin=False)
        # conn = estab_conn(f'{username}')
        # cur = conn.cursor()
        # searchresult = cur.execute(f'select * from uniquedata where id = \'{str(searchid)}\'').fetchone()
        print('shrimp', subtype, itemname, title, cph)
        cals = round(cph * (quantity/60))
        context.user_data['cals'] = cals
        activitytitle = f'{title} ({subtype})' if title != subtype else f'{title}'
        printstring = f'''activity details: 
{activitytitle}
{itemname}
{quantity} minutes, {cals} cals'''
        req_for_save = f'save activity to log or enter different quantity'

        keyboard = [[InlineKeyboardButton(text="enter a different quantity", callback_data='cq'),],
                    [InlineKeyboardButton(text=f"done, save to activity log", callback_data='save'), ],]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text=printstring)
        await update.message.reply_text(text=req_for_save, reply_markup=reply_markup)
        return SINGLE_ENTRY
    else:
        print('wtf, invalid type')

async def temp_yesno_cost(update: Update, context):
    itemname = context.user_data['itemname']
    ssunit = context.user_data['ssunit']
    quantity = context.user_data['quantity']

    if update.callback_query.data == 'yes':
        keyboard = [[InlineKeyboardButton(text="skip cost input", callback_data='no'),],]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=f'type a cost for {itemname}, {quantity} {ssunit}\nor skip cost input', reply_markup=reply_markup)
        return TYPING_COST
    elif update.callback_query.data == 'no':
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=f'skipping cost input')
        print('processing_food')
        itemname = context.user_data['itemname']
        searchid = context.user_data['searchid']
        subtype = context.user_data['subtype']
        title = context.user_data['activitytitle'] #persist
        tempdict = context.user_data['tempdict'] #persist
        calforappend = context.user_data['calquan']
        cpfforappend = context.user_data['cpfquan']
        cal = float(calforappend)
        print(itemname, quantity, ssunit, cal, title, tempdict)
        appendstring = '|'.join((str(searchid),str(itemname),str(quantity), str(calforappend), str(cpfforappend), str(ssunit))) #format a string to append to temp dict
        print(appendstring)
        tempdict.append(appendstring)
        context.user_data['tempdict'] = tempdict #resave temp dict
        printstring = f'''{itemname}: {quantity} {ssunit}, {cal} cal
{itemname} added to {title}'''
        req_for_save = f'would you like to add another food to {title}?'

        keyboard = [[InlineKeyboardButton(text="add another food", callback_data=subtype),],
                    [InlineKeyboardButton(text=f"done, save meal to activity log", callback_data='save'), ],]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=printstring)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=req_for_save, reply_markup=reply_markup)
        return FOOD_ADDORSAVE

async def process_cost(update: Update, context):

    precost = update.message.text
    re_string_dollaronly = '\d+$'
    re_string_dollarandcent = '\d+\.\d+'
    re_string_centonly = '\.\d+'
    dnc = re.search(re_string_dollarandcent, precost) #strictest search first
    cent = re.search(re_string_centonly, precost)
    dollar = re.search(re_string_dollaronly, precost)

    itemname = context.user_data['itemname']
    ssunit = context.user_data['ssunit']
    quantity = context.user_data['quantity']

    if dnc: #strictest search first
        x = dnc.group()
        cost = float(x)
    elif cent:
        x = cent.group()
        cost = float(x)
    elif dollar:
        x = dollar.group()
        cost = float(x)
    else:
        #invalid input
        keyboard = [[InlineKeyboardButton(text="re-enter cost", callback_data='cc'),],]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=f'invalid cost\n(try something like 10.52)\nclick \U0001F447 to re-enter cost', reply_markup=reply_markup)
        return CHANGE_COST

    context.user_data['cost'] = cost #save cost first
    print('processing_food')
    itemname = context.user_data['itemname']
    searchid = context.user_data['searchid']
    subtype = context.user_data['subtype']
    title = context.user_data['activitytitle'] #persist
    tempdict = context.user_data['tempdict'] #persist
    calforappend = context.user_data['calquan']
    cpfforappend = context.user_data['cpfquan']
    cal = float(calforappend)
    print(itemname, quantity, ssunit, cal, title, tempdict)
    appendstring = '|'.join((str(searchid),str(itemname),str(quantity), str(calforappend), str(cpfforappend), str(ssunit), str(cost))) #format a string to append to temp dict
    print(appendstring)
    tempdict.append(appendstring)
    context.user_data['tempdict'] = tempdict #resave temp dict
    printstring = f'''{itemname}: {quantity} {ssunit}, {cal} cal, ${str(cost)}
{itemname} added to {title}'''
    req_for_save = f'would you like to add another food to {title}?'

    keyboard = [[InlineKeyboardButton(text="add another food", callback_data=subtype),],
                [InlineKeyboardButton(text=f"done, save meal to activity log", callback_data='save'), ],]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text=printstring)
    await update.message.reply_text(text=req_for_save, reply_markup=reply_markup)
    return FOOD_ADDORSAVE

async def req_for_date(update: Update, context):
    #processes complete entries, print readable string, ask for date
    print(update.callback_query.data)
    maintype = context.user_data['maintype']
    subtype = context.user_data['subtype']
    title = context.user_data['activitytitle']
    printstring = ''
    try:
        if update.callback_query.data == 'cd':
            printstring = context.user_data['printstring']
    except:
        pass

    if not printstring:

        if maintype == 'food':
            itemlist = context.user_data['tempdict']
            itemdict = {}
            for i in itemlist:
                details = i.split('|')
                tempdict = {}
                tempdict['searchid'] = details[0]
                tempdict['itemname'] = details[1]
                tempdict['quantity'] = details[2]
                tempdict['calorie'] = details[3]
                tempdict['carbs'] = details[4]
                tempdict['protein'] = details[5]
                tempdict['fat'] = details[6]
                tempdict['quantityunit'] = details[7]
                try:
                    tempdict['cost'] = details[8]
                except:
                    tempdict['cost'] = 0
                itemdict[details[1]] = tempdict

            food_printstring = f'items for meal {title} ({subtype}):\n' if title != subtype else f'items for {title}:\n'
            caltotal = 0
            ctotal = 0
            ptotal = 0
            ftotal = 0
            money = 0
            x = 1
            for item in itemdict.values():
                searchid, itemname, quantity, calorie, carbs, protein, fat, quantityunit, cost = item.values()
                caltotal += float(calorie)
                ctotal += float(carbs)
                ptotal += float(protein)
                ftotal += float(fat)
                if float(cost) != 0:
                    money += float(cost)
                    item_printstring = f'''{x} - {itemname}, {str(quantity)} {quantityunit}, {str(calorie)}cal, ${str(cost)}
c: {str(carbs)}g, p: {str(protein)}g, f: {str(fat)}g, ${str(cost)}\n\n'''
                else:
                    item_printstring = f'''{x} - {itemname}, {str(quantity)} {quantityunit}, {str(calorie)}cal
c: {str(carbs)}g, p: {str(protein)}g, f: {str(fat)}g, ${str(cost)}\n\n'''
                x += 1
                food_printstring += item_printstring

            total_printstring = f'totals for {title}\ncals: {caltotal}cal, c: {str(ctotal)}g, p: {str(ptotal)}g, f:{str(ftotal)}g, ${str(money)}'
            food_printstring += total_printstring
            print(food_printstring)
            tytle = title
            printstring = food_printstring

        elif subtype == 'cardio' or subtype == 'sport':
            itemname = context.user_data['itemname']
            quantity = context.user_data['quantity']
            cals = context.user_data['cals']

            activitytitle = f'{title} ({subtype})' if title != subtype else f'{title}'
            cs_printstring = f'''activity details for {title}: 
{subtype} - {itemname}
{quantity} minutes, {cals} cals'''

            tytle = title
            printstring = cs_printstring

        elif subtype == 'gym':
            # appendstring = '|'.join((str(searchid),str(itemname),str(sets),str(reps),str(weight),str(pb),str(replace)))

            itemlist = context.user_data['tempdict']
            itemdict = {}
            x=1
            for i in itemlist:
                details = i.split('|')
                tempdict = {}
                tempdict['searchid'] = details[0]
                tempdict['itemname'] = details[1]
                tempdict['sets'] = details[2]
                tempdict['reps'] = details[3]
                tempdict['weight'] = details[4]
                tempdict['pb'] = details[5]
                tempdict['replace'] = details[6]
                itemdict[details[1]] = tempdict

            gym_printstring = f'items for workout {title}:\n' if title != subtype else f'items for workout:\n'
            for item in itemdict.values():
                searchid, itemname, sets, reps, weight, pb, replace = item.values()
                sets_reps_weight = f'{str(sets)}x{str(reps)} {str(weight)}kg' if float(weight)>0 else f'{str(sets)}x{str(reps)}'
                if str(pb) == 'true' and str(replace) == 'true':
                    item_printstring = f'''{x} - {itemname}\n{sets_reps_weight} (PB)\n\n'''
                else:
                    item_printstring = f'''{x} - {itemname}\n{sets_reps_weight}\n\n'''
                gym_printstring += item_printstring
                x += 1


            tytle = title
            printstring = gym_printstring
            print(gym_printstring)


    print(printstring)
    context.user_data['printstring'] = printstring


    x = 'food' if maintype == 'food' else 'se' if subtype == 'cardio' or subtype == 'sport' else 'lift'

    if x == 'food' or x == 'lift':
        y = 'meal' if x == 'food' else 'workout'
        keyboard = [[InlineKeyboardButton(text="today", callback_data='tdy'), InlineKeyboardButton(text=f"yesterday", callback_data='ytd'), ],
                    [InlineKeyboardButton(text=f"add another {x}", callback_data=x),],]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(printstring)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'choose a date for {tytle} \n\nor add another {x} to {y}', reply_markup=reply_markup)

    else:
        keyboard = [[InlineKeyboardButton(text="today", callback_data='tdy'),],
                    [InlineKeyboardButton(text=f"yesterday", callback_data='ytd'), ],]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(printstring)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'choose a date for {tytle}', reply_markup=reply_markup)

    return SELECTING_DATE

async def req_for_time(update: Update, context):
    print('here1')
    if update.callback_query.data == 'ytd' or update.callback_query.data == 'tdy': #forward date call
        print('here1')
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days = 1)
        if update.callback_query.data == 'ytd':
            datestr = yesterday.strftime('%d-%m-%Y')
        else:
            datestr = today.strftime('%d-%m-%Y')
        print(datestr)
        context.user_data['datestr'] = datestr #save date string
    elif update.callback_query.data == 'ct':
        try:
            datestr = context.user_data['datestr'] #retrieve saved date string if its a backwards call
        except:
            print('fail')

    keyboard = [[InlineKeyboardButton(text="change date", callback_data='cd'),],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(f'selected date: {datestr}')
    await context.bot.send_message(chat_id=update.effective_chat.id, text='enter an activity time in HH:MM format\n\nor click \U0001F447 to rechoose date', reply_markup=reply_markup)

    return TYPING_TIME

async def process_time(update: Update, context):
    timestr = update.message.text
    try:
        datetime.datetime.strptime(timestr, '%H:%M')
        datestr = context.user_data['datestr']
        fulltime = datestr + ', ' + timestr
        print(fulltime)
        context.user_data['timestamp'] = fulltime
    except:
        keyboard = [[InlineKeyboardButton(text="re-enter time", callback_data='ct'),],]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('invalid input - \nclick \U0001F447 to re-enter time', reply_markup=reply_markup)
        return CONFIRMING_TIME

    keyboard = [[InlineKeyboardButton(text="yes - save activity", callback_data='save'),],[InlineKeyboardButton(text="re-enter time", callback_data='ct'),]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'confirm activity timestamp: \n{fulltime}', reply_markup=reply_markup)

    return CONFIRMING_TIME

async def save_activity(update: Update, context):
    maintype = context.user_data['maintype']
    subtype = context.user_data['subtype']
    title = context.user_data['activitytitle']

    if maintype == 'food':
        itemlist = context.user_data['tempdict']
        itemdict = {}
        for i in itemlist:
            details = i.split('|')
            tempdict = {}
            tempdict['searchid'] = details[0]
            tempdict['itemname'] = details[1]
            tempdict['quantity'] = details[2]
            tempdict['calorie'] = details[3]
            tempdict['carbs'] = details[4]
            tempdict['protein'] = details[5]
            tempdict['fat'] = details[6]
            tempdict['quantityunit'] = details[7]
            try:
                tempdict['cost'] = details[8]
            except:
                tempdict['cost'] = 0
            itemdict[details[1]] = tempdict

        food_printstring = f'items for meal {title} ({subtype}):\n' if title != subtype else f'items for {title}:\n'
        caltotal = 0
        ctotal = 0
        ptotal = 0
        ftotal = 0
        money = 0
        x = 1
        namecaldict = {}
        for item in itemdict.values():
            searchid, itemname, quantity, calorie, carbs, protein, fat, quantityunit, cost = item.values()
            caltotal += float(calorie)
            ctotal += float(carbs)
            ptotal += float(protein)
            ftotal += float(fat)
            # shorteneditemname = itemname.split[', ']
            # namecaldict[shorteneditemname] = round(float(calorie))
            if float(cost) != 0:
                money += float(cost)
                item_printstring = f'''{x} - {itemname}, {str(quantity)} {quantityunit}, {str(calorie)}cal, ${str(cost)}
c: {str(carbs)}g, p: {str(protein)}g, f: {str(fat)}g, ${str(cost)}\n\n'''
            else:
                item_printstring = f'''{x} - {itemname}, {str(quantity)} {quantityunit}, {str(calorie)}cal
c: {str(carbs)}g, p: {str(protein)}g, f: {str(fat)}g, ${str(cost)}\n\n'''
            x += 1
            food_printstring += item_printstring


        description = f'P: {ptotal}g, C:{ctotal}g, F: {ftotal}g'
        total_printstring = f'totals for {title}\ncals: {caltotal}cal, c: {str(ctotal)}g, p: {str(ptotal)}g, f:{str(ftotal)}g, ${str(money)}'
        food_printstring += total_printstring
        print(food_printstring)
        tytle = title
        printstring = food_printstring

    elif subtype == 'cardio' or subtype == 'sport':
        itemname = context.user_data['itemname']
        quantity = context.user_data['quantity']
        calorie = context.user_data['cals']

        activitytitle = f'{title} ({subtype})' if title != subtype else f'{title}'
        cs_printstring = f'''activity details for {title}: 
{subtype} - {itemname}
{quantity} minutes, {calorie} cals'''
        description = subtype + ' - '  + itemname
        tytle = title
        printstring = cs_printstring

    elif subtype == 'gym':
        # appendstring = '|'.join((str(searchid),str(itemname),str(sets),str(reps),str(weight),str(pb),str(replace)))

        itemlist = context.user_data['tempdict']
        itemdict = {}
        x=1
        for i in itemlist:
            details = i.split('|')
            tempdict = {}
            tempdict['searchid'] = details[0]
            tempdict['itemname'] = details[1]
            tempdict['sets'] = details[2]
            tempdict['reps'] = details[3]
            tempdict['weight'] = details[4]
            tempdict['pb'] = details[5]
            tempdict['replace'] = details[6]
            itemdict[details[1]] = tempdict

        gym_printstring = f'items for workout {title}:\n' if title != subtype else f'items for workout:\n'
        groupdict = {}
        for item in itemdict.values():
            searchid, itemname, sets, reps, weight, pb, replace = item.values()
            sets_reps_weight = f'{str(sets)}x{str(reps)} {str(weight)}kg' if float(weight)>0 else f'{str(sets)}x{str(reps)}'
            if str(pb) == 'true' and str(replace) == 'true':
                item_printstring = f'''{x} - {itemname}\n{sets_reps_weight} (PB)\n\n'''
            else:
                item_printstring = f'''{x} - {itemname}\n{sets_reps_weight}\n\n'''
            gym_printstring += item_printstring
            group = itemname.split(', ')[-1]
            if group in groupdict.keys():
                groupdict[group] += 1
            else:
                groupdict[group] = 1
            x += 1

        sorted_groups_by_hits = sorted(groupdict.items(), key=lambda x:x[1], reverse=True)
        descriptionpre = ''
        print(sorted_groups_by_hits)
        for item in sorted_groups_by_hits[0:3]:
            descriptionpre += ', ' + item[0]
        description = descriptionpre[2:]

        calorie = 0
        tytle = title
        printstring = gym_printstring


    sql_dtg = str(context.user_data['timestamp'])
    sql_subtype = str(subtype)
    sql_title = title
    sql_calorie = str(calorie)
    sql_description = description
    sql_cost = str(cost) if maintype == 'food' else '0'
    sql_printstring = printstring

    try:
        user = update.message.from_user
    except:
        user = update.callback_query.from_user
    userid = user['id'] #get username from userid
    username = verify_if_account_exists(userid, context, prin=False) #get username from viae and prevents message send
    try:
        
        sql = f'INSERT INTO activitylog_{username} (dtg, subtype, title, calorie, description, cost, printstring) VALUES (%s,%s,%s,%s,%s,%s,%s)'
        execute_pgsql(sql, (sql_dtg, sql_subtype, sql_title, sql_calorie, sql_description, sql_cost, sql_printstring))
        
        print(sql_dtg, sql_subtype, sql_title, sql_calorie, sql_description, sql_cost, sql_printstring)
        print(f'successful input of {sql_title} for {username}')
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(f'successfully added {sql_title} to activity log')
        #CLEAR CACHE
        context.user_data['tempdict'] = {}
        context.user_data['maintype'] = ''
        context.user_data['subtype'] = ''
        context.user_data['activitytitle'] = ''
        context.user_data['itemname'] = ''
        context.user_data['quantity'] = ''
        context.user_data['cals'] = ''
        try:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text('exiting newactivity \ntype /help to view available functions')
        except:
            await update.message.reply_text('exiting newactivity \ntype /help to view available functions')
        return END
    except Exception as e:
        print('saveactivity fail with exception', e)

async def exit(update: Update, context):
    print('in exit')
    try:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text('exiting newactivity \ntype /help to view available functions')
    except:
        await update.message.reply_text('exiting newactivity \ntype /help to view available functions')
    return END

async def testfunction(update: Update, context):
    print(f'testfunction printing {update.message.text}')

async def testfunction2(update: Update, context):
    print(f'testfunction2 printing {update.message.text}')

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('newactivity', newactivity)],
    states={
        SELECTING_SUBTYPE: [CallbackQueryHandler(req_for_title, pattern='^(breakfast|snack|lunch|dinner|cardio|sport|gym)$')],
        TYPING_STRING: [CallbackQueryHandler(newactivity, pattern='^(reselect_subtype)$'), MessageHandler(filters.TEXT & ~filters.COMMAND, select_option)],
        TYPING_TYTLE: [CallbackQueryHandler(req_for_search, pattern='^(skip_title)$'), MessageHandler(filters.TEXT & ~filters.COMMAND, req_for_search)],
        SELECTING_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_for_quantity), CallbackQueryHandler(req_for_search, pattern='^(breakfast|snack|lunch|dinner|cardio|sport|gym)$')],
        INVALID_OPTION: [CallbackQueryHandler(select_option, pattern='^(sdo)$')],
        SELECTING_REPLACE: [CallbackQueryHandler(temp_yesno_replace, pattern='^(yes|no)$'), CallbackQueryHandler(select_option, pattern='^(sdo)$')],
        TYPING_SETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_for_reps), CallbackQueryHandler(select_option, pattern='^(sdo)$')],
        TYPING_REPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_for_weight), CallbackQueryHandler(req_for_quantity, pattern='^(cq)$')],
        TYPING_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_weight), CallbackQueryHandler(req_for_reps, pattern='^(cr)$')],
        CONFIRMING_WEIGHT: [CallbackQueryHandler(process_lift, pattern='^(yes)$'),CallbackQueryHandler(req_for_weight, pattern='^(cw)$')],
        GYM_ADDORSAVE: [CallbackQueryHandler(req_for_search, pattern='^(breakfast|snack|lunch|dinner|cardio|sport|gym)$'),CallbackQueryHandler(req_for_date, pattern='^(save)$')],
        TYPING_QU4NTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_quantity), CallbackQueryHandler(select_option, pattern='^(sdo)$')],
        CHANGE_QUANTITY: [CallbackQueryHandler(req_for_quantity, pattern='^(cq)$')],
        SINGLE_ENTRY: [CallbackQueryHandler(req_for_quantity, pattern='^(cq)$'),CallbackQueryHandler(req_for_date, pattern='^(save)$')],
        COST_YESNO: [CallbackQueryHandler(req_for_quantity, pattern='^(cq)$'), CallbackQueryHandler(temp_yesno_cost, pattern='^(yes|no)$')],
        FOOD_ADDORSAVE: [CallbackQueryHandler(req_for_search, pattern='^(breakfast|snack|lunch|dinner|cardio|sport|gym)$'),CallbackQueryHandler(req_for_date, pattern='^(save)$')],
        TYPING_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_cost), CallbackQueryHandler(temp_yesno_cost, pattern='^(no)$')],
        CHANGE_COST: [CallbackQueryHandler(temp_yesno_cost, pattern='^(cc)$')],
        SELECTING_DATE: [CallbackQueryHandler(req_for_time, pattern='^(ytd|tdy)$'), CallbackQueryHandler(req_for_search, pattern='^(food|lift)$')],
        TYPING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_time), CallbackQueryHandler(req_for_date, pattern='cd')],
        CONFIRMING_TIME: [CallbackQueryHandler(save_activity, pattern='^(save)$'), CallbackQueryHandler(req_for_time, pattern='ct')]
    },
    fallbacks=[CommandHandler("help", telehelp), CommandHandler("exit", exit)]
)

#######################END OF CONV HANDLER####################


#######################CONV HANDLER 2 - FOR NEW DATABASE ENTRY####################


# State definitions for states (initial states before split for gym
SELECTING_SUBTYPE2, TYPING_TITLE2, TYPING_QU4NTITY2, SAVE_OR_EDIT = map(chr, range(4))
END = ConversationHandler.END

async def customentry(update: Update, context):
    try:
        query = update.callback_query #check for callback query
        data = query.data
        if data == 'reselect_subtype': #if there is callbackquery data, it means its a backwards call, so just display the buttons again for user to click
            user = update.callback_query.from_user
            print('user ID: {}, called /customentry'.format(user['username']))
            title = context.user_data['entrytitle']

        buttons = [
            [
                InlineKeyboardButton(text="food", callback_data='food'),
                InlineKeyboardButton(text="cardio", callback_data='cardio'),
            ],
            [

                InlineKeyboardButton(text="sport", callback_data='sport'),
                InlineKeyboardButton(text="lift", callback_data='lift'),
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text='select entry type', reply_markup=keyboard) #ask user to click button to select activity type
        return SELECTING_SUBTYPE2
    except:
        user = update.message.from_user
        print('user ID: {}, called /customentry'.format(user['username']))
        if verify_if_account_exists(user['id'], context, update=update):
            buttons = [
                [
                    InlineKeyboardButton(text="food", callback_data='food'),
                    InlineKeyboardButton(text="cardio", callback_data='cardio'),
                ],
                [

                    InlineKeyboardButton(text="sport", callback_data='sport'),
                    InlineKeyboardButton(text="lift", callback_data='lift'),
                ],
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            await update.message.reply_text(text='select entry type     ', reply_markup=keyboard) #ask user to click button to select activity type
            return SELECTING_SUBTYPE2

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='you have not created an account yet \n\n type /username <your username> to create an account \n\nlike this: /username user1.')


async def req_for_titletwo(update: Update, context):
    subtype = update.callback_query.data
    if subtype == 'food':
        maintype = 'food'
    else:
        maintype = 'workout'
    context.user_data['maintype'] = maintype #save type in user data
    context.user_data['subtype'] = subtype #save subtype in user data

    subtype_string = subtype if maintype == 'food' else str(subtype + ' activity')
    message = f'enter a title for your custom {subtype}'
    keyboard = [[InlineKeyboardButton("macro calculator", url = 'https://www.healthline.com/health/what-are-mets'),]]
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=message)

    return TYPING_TITLE2

async def req_for_quantitytwo(update: Update, context):
    try:
        entrytitle = update.message.text
        context.user_data['entrytitle'] = entrytitle
    except:
        entrytitle = context.user_data['entrytitle']
    subtype = context.user_data['subtype']
    if subtype == 'food':
        text = f'for {entrytitle}, enter comma-separated values for \nserving size, serving size unit, calories per serving, carbs, protein, and fat\n\nexample: 25, g, 170, 10, 10, 10'
        keyboard = [[InlineKeyboardButton("change title", callback_data=subtype),]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # await update.message.reply_text(text, reply_markup=reply_markup)
    elif subtype == 'sport' or subtype == 'cardio':
        text = f'enter mets for {entrytitle}\n\nexample: 7.5'
        keyboard = [[InlineKeyboardButton("what are mets?", url = 'https://www.healthline.com/health/what-are-mets'),], [InlineKeyboardButton("change title", callback_data=subtype),]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # await update.message.reply_text(text, reply_markup=reply_markup)
    elif subtype == 'lift':
        text = f'for {entrytitle}, enter comma-separated values for \nprimary muscle group, pb weight, pb reps, pb sets\n\nexample: chest, 60, 5, 5'
        keyboard = [[InlineKeyboardButton("change title", callback_data=subtype),]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # await update.message.reply_text(text, reply_markup=reply_markup)

    try:
        await update.message.reply_text(text, reply_markup=reply_markup)
    except:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    return TYPING_QU4NTITY2

async def process_quantitytwo(update: Update, context):
    u = update.message.text
    entrytitle = context.user_data['entrytitle']
    subtype = context.user_data['subtype']

    def datacheck(subtype, u):
        if subtype == 'food':
            data = u.split(',')
            if len(data) != 6:
                return False
            else:
                for i in range(len(data)):
                    if i != 1:
                        try:
                            float(data[i].strip())
                        except:
                            return False
        elif subtype == 'cardio' or subtype == 'sport':
            data = u
            try:
                float(u)
            except Exception as e:
                print(e)
                return False
        elif subtype == 'lift':
            data = u.split(',')
            if len(data) != 4:
                return False
            else:
                for i in range(len(data)):
                    if i != 0:
                        try:
                            float(data[i].strip())
                        except:
                            return False
                    elif i == 0:
                        default = False
                        groups = ['biceps', 'triceps', 'shoulders', 'chest', 'back', 'legs', 'abs', 'forearms', 'grip']
                        for x in groups:
                            if x in data[i]:
                                default = True
                                context.user_data['group'] = x
                                break
                        if not default:
                            return 'x'
        return True

    print(datacheck(subtype, u))
    if datacheck(subtype, u):
        if subtype == 'food':
            data = [x.strip() for x in u.split(',')]
            print(data)
            print([float(x) for x in data[3:]])
            servingsize = float(data[0])
            servingsizeunit = str(data[1])
            cal = int(data[2])
            c, p, f = tuple([float(x) for x in data[3:]])
            context.user_data['servingsize'] = servingsize
            context.user_data['servingsizeunit'] = servingsizeunit
            context.user_data['cal'] = cal
            context.user_data['cpf'] = ', '.join([str(x) for x in [c, p, f]])
            selected_message = f'new {subtype}: {entrytitle}\n{servingsize} {servingsizeunit}, {cal} cal\nc: {c}g, p: {p}g, f: {f}g'
            message = f'save to my database or edit data'
        elif subtype == 'cardio' or subtype == 'sport':
            context.user_data['cal'] = u.strip()
            mets = float(u)
            selected_message = f'new {subtype}: {entrytitle}, {mets} mets'
            message = f'save to my database or edit data'
        elif subtype == 'lift':
            data = [x.strip() for x in u.split(',')]
            group = context.user_data['group']
            weight = float(data[1])
            reps = float(data[2])
            sets = int(data[3])
            newentrytitle = entrytitle + f', {group}'
            context.user_data['entrytitle'] = newentrytitle
            context.user_data['servingsize'] = sets
            context.user_data['servingsizeunit'] = weight
            context.user_data['cal'] = reps
            selected_message = f'new {subtype}: {newentrytitle}:\n{str(sets)}x{str(reps)} {weight} kg'
            message = f'save to my database or edit data'

        keyboard = [[InlineKeyboardButton("save new entry", callback_data='save_entry'),],
                    [InlineKeyboardButton("edit data", callback_data='edit_data'),]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(selected_message)
        await update.message.reply_text(message, reply_markup=reply_markup)

    else:
        if datacheck(subtype, u) == 'x':
            keyboard = [[InlineKeyboardButton("edit data", callback_data='edit_data'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            groups = ['biceps', 'triceps', 'shoulders', 'chest', 'back', 'legs', 'abs', 'forearms', 'grip']
            groupstring = '/'.join(groups)
            await update.message.reply_text(f'invalid muscle group, options:\n{groupstring}', reply_markup=reply_markup)
            return SAVE_OR_EDIT
        else:
            keyboard = [[InlineKeyboardButton("edit data", callback_data='edit_data'),]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f'invalid data', reply_markup=reply_markup)

    return SAVE_OR_EDIT


async def save_entry(update: Update, context):
    subtype = context.user_data['subtype']
    entrytitle = context.user_data['entrytitle']
    entrytitle = subtype + ', ' + entrytitle
    print('save entry subtype', subtype)
    print(entrytitle)
    if subtype == 'food':
        quantity = context.user_data['servingsize']
        quantityunit = context.user_data['servingsizeunit']
        cal = context.user_data['cal']
        c,p,f = context.user_data['cpf'].split(', ')
        cpf = f'C: {c}g, P: {p}g, F: {f}g'
        # food_printstring = f'new {subtype}: {entrytitle}, {quantity} {quantityunit}\ncals: {cal}cal, c: {str(c)}g, p: {str(p)}g, f:{str(f)}g}'
        # printstring = food_printstring

    elif subtype == 'cardio' or subtype == 'sport':
        mets = context.user_data['cal']
        quantity = '60'
        quantityunit = 'mins'
        cal = mets
        cpf = ''

        # cs_printstring = f'new {subtype}: {entrytitle}, {mets} mets'
        # printstring = cs_printstring

    elif subtype == 'gym':
        sets = context.user_data['servingsize']
        weight = context.user_data['servingsizeunit']
        reps = context.user_data['cal']
        quantity = sets
        quantityunit = weight
        cal = reps
        cpf = f''
        # food_printstring = f'new {subtype}: {entrytitle}, {quantity} {quantityunit}\ncals: {cal}cal, c: {str(c)}g, p: {str(p)}g, f:{str(f)}g}'
        # printstring = gym_printstring


    sql_title = entrytitle
    sql_quantity = quantity
    sql_quantityunit = quantityunit
    sql_calorie = str(cal)
    sql_cpf = cpf

    try:
        user = update.message.from_user
    except:
        user = update.callback_query.from_user
    userid = user['id'] #get username from userid
    username = verify_if_account_exists(userid, context, prin=False) #get username from viae and prevents message send

    try:
        

        sql = f'INSERT INTO uniquedata_{username} (name, quantity, quantityunit, calorie, cpf) VALUES(%s,%s,%s,%s,%s)'
        execute_pgsql(sql, (sql_title, sql_quantity, sql_quantityunit, sql_calorie, sql_cpf))
        
        print(f'successful input of {sql_title} for {username}')
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(f'successfully added {sql_title} to database')
        send_to_admin(f'user {username} added {entrytitle}, {subtype} to own database')
        #CLEAR CACHE
        return END
    except Exception as e:
        print(e)

conv_handler2 = ConversationHandler(
    entry_points=[CommandHandler('customentry', customentry)],
    states={
        SELECTING_SUBTYPE2: [CallbackQueryHandler(req_for_titletwo, pattern='^(food|cardio|sport|lift)$')],
        TYPING_TITLE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_for_quantitytwo)],
        TYPING_QU4NTITY2: [CallbackQueryHandler(req_for_titletwo, pattern='^(food|cardio|sport|lift)$'), MessageHandler(filters.TEXT & ~filters.COMMAND, process_quantitytwo)],
        SAVE_OR_EDIT: [CallbackQueryHandler(save_entry, pattern='save_entry'), CallbackQueryHandler(req_for_quantitytwo, pattern='edit_data')]
    },
    fallbacks=[CommandHandler("help", telehelp), CommandHandler("exit", exit), CallbackQueryHandler(exit)]
)


###############################END OF CONV HANDLER2 ######################




if __name__ == '__main__':




    print(f'running at handler level. time: {datetime.datetime.now()}')

    send_to_admin(f'tele.py running started at time: {datetime.datetime.now()}')
    start_handler = CommandHandler('start', start)
    # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    username_handler = CommandHandler('username', username)
    setmacros_handler = CommandHandler('setmacros', setmacros)
    setbcg_handler = CommandHandler('setbcg', setbcg)
    setp_handler = CommandHandler('setp', setp)
    setf_handler = CommandHandler('setf', setf)
    setc_handler = CommandHandler('setc', setc)
    setw_handler = CommandHandler('setw', setw)
    updateweight_handler = CommandHandler('updateweight', updateweight)
    help_handler = CommandHandler('help', telehelp)
    viewlog_handler = CommandHandler('viewlog', viewlog)
    viewmacros_handler = CommandHandler('viewmacros', viewmacros)
    viewgym_handler = CommandHandler('viewgym', viewgympri)
    choosegroup_handler = CallbackQueryHandler(viewgymhandle, pattern='biceps|triceps|shoulders|chest|back|abs|legs')
    test_handler = CommandHandler('test', testfunction)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    print(f'running at addhandler level. time: {datetime.datetime.now()}')
    application.add_handler(start_handler)
    application.add_handler(username_handler)
    # application.add_handler(echo_handler)
    application.add_handler(setmacros_handler)
    application.add_handler(setbcg_handler)
    application.add_handler(setc_handler)
    application.add_handler(setw_handler)
    application.add_handler(updateweight_handler)
    application.add_handler(setp_handler)
    application.add_handler(setf_handler)
    application.add_handler(viewlog_handler)
    application.add_handler(viewmacros_handler)
    application.add_handler(viewgym_handler)
    application.add_handler(choosegroup_handler)
    application.add_handler(conv_handler)
    application.add_handler(conv_handler2)
    application.add_handler(help_handler)
    application.add_handler(test_handler)
    application.add_handler(unknown_handler)
    application.add_handler(CallbackQueryHandler(testhandlerfunction))

    print(f'tele.py running completed at time: {datetime.datetime.now()}')
    application.run_polling()
    print('here')
