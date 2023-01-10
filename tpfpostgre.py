import sqlite3
import datetime
import re
import sys
import psycopg2
import requests


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
#called during username creation (tele user call: /username <username>)
def username_validation(username,userid):
    '''checks if username already exists in userdata.db, if username available, creates new user, returns False, if user'''
    username_available = False

    #called when we have ascertained that username does not exist
    #creates new table for new user in userdata database and enters it into allusers with userid tagged to username
    #creates new database for new user called activity_<username> and initialises an allentries table (refer to activity.db for explanation)
    def usernamedoesnotexist():
        try:
            #sql - create unique user activitylog
            sql = f'CREATE TABLE activitylog_{username} (id SERIAL PRIMARY KEY, dtg TEXT, subtype TEXT, title TEXT, calorie INT, description TEXT, cost REAL, printstring TEXT)'
            execute_pgsql(sql)
            sql2 = f'CREATE TABLE uniquedata_{username} (id SERIAL PRIMARY KEY, name TEXT, quantity REAL, quantityunit TEXT, calorie REAL, cpf TEXT)'
            execute_pgsql(sql2)

            try:
                usernamewithtracking = 'tracking_' + username #create name of table to search for (formatted as tracking_username)
                sql = f'''CREATE TABLE IF NOT EXISTS {usernamewithtracking} (
            "date"	TEXT,
            "calin"	INT,
            "calout"	INT,
            "carbsin"	INT,
            "carbtarget"	INT,
            "protin"	INT,
            "prottarget"	INT,
            "fatin"	INT,
            "fattarget"	INT,
            "weight"	REAL,
            "weighttarget"	REAL,
            "money"	REAL) '''
                execute_pgsql(sql)
                execute_pgsql(f'INSERT INTO {usernamewithtracking} (date, weight) VALUES(%s, %s)', ('default', 60.0))
                execute_pgsql('INSERT INTO all_users VALUES(%s,%s)',(userid, username))


                conn3 = sqlite3.connect('basedata.db')
                cur3 = conn3.cursor()
                #get alldata rows from basedata
                data = cur3.execute('SELECT * FROM alldata').fetchall()
                print(data)
                DB_URL = "postgresql://postgres:ZvoYvy6Lp78aZm2MBk5p@containers-us-west-155.railway.app:7864/railway"
                conn = psycopg2.connect(DB_URL, sslmode='require')
                cursor = conn.cursor()

                records_list_template = ','.join(['%s'] * len(data))
                insert_query = 'insert into uniquedata_{} (name, quantity, quantityunit, calorie, cpf) values {}'.format(username, records_list_template)
                cursor.execute(insert_query, data)

                conn3.close()
                conn.commit()
                cursor.close()
                conn.close()
                
                send_to_admin(f'created new tracking table for {username} and inserted {username} into all_users tagged to {userid}')
            except Exception as e:
                print('newusercreationfail:', e)
                
        except Exception as e:
            print('newusercreationfail', e)
        else:
            print(f'new user {username} created')


    #look for username in all_users username column
    #if cannot find,
    usernamelistpre = execute_pgsql(f'SELECT username FROM all_users',fetchall=True)
    if usernamelistpre:
        usernamelist = [x[0] for x in usernamelistpre]
    else:
        usernamelist = []
    print('list of usernames: ', usernamelist)
    if username in usernamelist:
        pass #if username exists, leave return value as False (i.e. username not available)
    else:
           username_available = True #if username is not in userlist - set username_available to True
           #execute username does not exist function
                #creates new unique tracking_<username> table in userdata
                #creates new allusers entry with userid tagged to username
                #creates new database for new user called <username> and initialises activitylog and uniquedata tables
                #imports basedata into unique data
           usernamedoesnotexist()

    #prints to console to let admin know function was called for what username and returned what result
    print(f'username_validation called and returned username_available={username_available} for username: {username}')
    return username_available

#called to check if user has made account before (tele user call --> /start) -- returns username if userid exists and False if not
def userid_exists(userid):
    '''checks if userid is already in userdata.db, if it is return username associated with userid, if not return False'''
    userid_exists = False

    result = execute_pgsql(f"SELECT * FROM all_users WHERE userid = {userid}",fetchall=True)

    if not result: #userid not in userdata.db -- leave return value as False (user id does not exist)
        pass
    elif len(result) == 1: #userid is in userdata.db -- change return value to username associated with userid
        userid_exists = result[0][1]
    else: #somehow more than one userid but highly unlikely since primary key
        print('we got big problems')

    print(f'userid_exists check for {userid} and returned userid_exists as: {userid_exists}')
    return userid_exists

#called to check if user has set their macros before (tele usercall --> /setmacros)
def usermacros_created(userid):
    '''checks if user has entered their base calorie goal before -- return True if they have'''
    returnvalue = False

    username = execute_pgsql(f"SELECT username FROM all_users WHERE userid = {userid}",fetchone=True)[0] #find username based on user_id
        
    usernamewithtracking = 'tracking_' + username #create name of table to search for (formatted as tracking_username)

    #retrieve default calout value to check if bcg has been entered before
    result = execute_pgsql(f'SELECT calout FROM {usernamewithtracking} WHERE date=\'default\'', fetchall=True)[0][0]
    print(result)
    if result: #calout has been set before
        returnvalue = True
    else: #calout has not been set before
        pass
    print(f'usermacros_created called by {username} and returned {returnvalue}')
    return returnvalue

#inserts default macro value for whatever macro and whatever userid
def sql_set_defaultmacro(macro, value, userid):
    try:
        username = execute_pgsql(f'SELECT username FROM all_users WHERE userid=\'{userid}\'',fetchone=True)[0]
        
        usernamewithtracking = 'tracking_' + username
        sql = f'UPDATE {usernamewithtracking} SET {macro} = %s WHERE date = %s'
        execute_pgsql(sql, (value, 'default'))
        print(f'update {macro} to {value} success for user {username} ')
        return 'true'
    except Exception as e:
        print(f'insert macro fail with exception {e}')
        return 'false', e

def display_macros(username):
    datetoday, calin, calout, carbsin, carbtarget, protin, prottarget, fatin, fattarget, weight, money = log_macros(username, autocall=False)
    calremaining = calout - calin
    calbase = get_defaults(username, 'calout')
    print(calbase)
    # Parse the date string
    date = datetime.datetime.strptime(datetoday, "%d-%m-%Y")
    if not carbtarget:
        carbtarget = 0
    if not prottarget:
        prottarget = 0
    if not fattarget:
        fattarget = 0
    if not calbase:
        calbase = 0

    # Format the date using the strftime() method
    datedisplay = date.strftime("%A, %d-%m-%Y")
    print('xxxxxx', datetoday)
    printstring = f'''{datedisplay}
Calories remaining:\t\t{round(calremaining)} cal
Base Goal:\t\t{round(calbase)} cal
Food:\t\t{round(calin)} cal
Exercise:\t\t{round(calout-calbase)} cal
Protein:\t\t{round(protin)}/{prottarget} g
Carbs:\t\t{round(carbsin)}/{carbtarget} g
Fat:\t\t{round(fatin)}/{fattarget} g'''

    return printstring

# log daily values - autorun at 2359
def log_macros(username, autocall = False, datedifferent=False):
    '''retrieves targets and input values for the day and returns as tuple, if autocall is true then log as daily input value (2359 log)'''
  
    print('datedifferent', datedifferent)
    if datedifferent:
        datetoday = datedifferent.strftime("%d-%m-%Y" )
    else:
        datetoday = datetime.datetime.now().strftime("%d-%m-%Y" )
    print('datetoday:', datetoday)
    calin, calout, carbsin, protin, fatin, money = display_activity_log(username, display=False, datedifferent=datetoday)
    carbtarget = get_defaults(username, 'carbtarget')
    prottarget = get_defaults(username, 'prottarget')
    fattarget = get_defaults(username, 'fattarget')
    weighttarget = get_defaults(username, 'weighttarget')
    weight = get_defaults(username, 'weight')
    print(autocall)
    if autocall: #if auto call (insert into db)
        try:
            weightsql = f"SELECT weight from tracking_{username} where date LIKE '{datetoday}'"
            weightretrieved = execute_pgsql(weightsql, fetchone=True)
            if bool(weightretrieved):
                weight = weightretrieved[0]
            else:
                x = 1
                while x > 0:
                    sql2 = f'SELECT weight FROM tracking_{username} ORDER BY date DESC LIMIT {x}' #if no weight use last inserted weight until default reached
                    w = execute_pgsql(sql2,fetchall=True)[-1][0]
                    if 10.0 < w < 200.0:
                        weight = w
                        x = 0
                    else:
                        x += 1

            presql = f'DELETE FROM tracking_{username} where date LIKE \'{datetoday}\''
            print(presql)
            execute_pgsql(presql)
            testsql = f'SELECT * FROM tracking_{username} where date LIKE \'{datetoday}\''
            test = execute_pgsql(testsql, fetchone=True)
            print(test)
            sql = f'INSERT INTO tracking_{username} VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            execute_pgsql(sql, (datetoday, calin, calout, carbsin, carbtarget, protin, prottarget, fatin, fattarget, weight, weighttarget, money))
            print(f'data logged for day: {datetoday}')
        except Exception as e:
            print('logmacros',e)
            pass
    #if not simply return values requested
    else:
        print(datetoday, calin, calout, carbsin, carbtarget, protin, prottarget, fatin, fattarget, weight, money)
        return datetoday, calin, calout, carbsin, carbtarget, protin, prottarget, fatin, fattarget, weight, money

def get_defaults(username, macro):
    sql = f'SELECT {macro} FROM tracking_{username} WHERE date = \'default\''
    try:
        macrovalue = execute_pgsql(sql,fetchone=True)[0]
    except Exception as e:
        macrovalue = 0
        print(e)
    return macrovalue


#find all activities from today and either return fetchall object or False
def fetch_today_activity(username, datedifferent=False):
    if datedifferent:
        todaydtg = datedifferent
    else:
        todaydtg = datetime.datetime.now().strftime("%d-%m-%Y" )
    sql = f'SELECT * FROM activitylog_{username} WHERE dtg LIKE \'{todaydtg}%\''  #get all todays activities from user's activitylog
    dayactivitylog = False
    try:
        dayactivitylog = execute_pgsql(sql,fetchall=True)
    except:
        pass
    return dayactivitylog

def display_activity_log(username, display, datedifferent=False):
    def get_mac_from_desc(description):
        def get_p_from_desc(description):
            p_pattern = 'P:.+g, C'
            p_pattern2 = 'P:.+g,'
            p_pattern3 = '\d.+\d'
            match = re.search(p_pattern, description).group()
            match2 = re.search(p_pattern2, match).group()
            match3 = re.search(p_pattern3, match2).group()
            return float(match3)

        def get_c_from_desc(description):
            c_pattern = 'C:.+g,'
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

    if datedifferent:
        dayactivitylog = fetch_today_activity(username, datedifferent)
    else:
        dayactivitylog = fetch_today_activity(username) #fetch all activities from today first

    if dayactivitylog:
        calin = 0
        calout = get_defaults(username, 'calout')
        p = 0
        c = 0
        f = 0
        money = 0
        # print('dayactivitylog', dayactivitylog)

        #format date (get dtg from first entry) for printing
        dtg = dayactivitylog[0][1]
        print(dtg, dtg[:-6])
        datepredisplay = datetime.datetime.strptime(dtg[:-7], "%d-%m-%Y")
        datedisplay = datetime.datetime.strftime(datepredisplay, "%d-%m-%Y")

        finalstring = f'Activity log for {datedisplay}\n' #initialise final string to be displayed
        sepstring = '-' * 25 + '\n' #create separator string to use between entries
        finalstring += sepstring #concat separator string to intro string

        for i in dayactivitylog:
            finalstring += sepstring #before adding each printstring, add separator string
            dtg, subtype, title, calorie, description, cost = i[1], i[2], i[3], i[4], i[5], i[6]
            timepredisplay = datetime.datetime.strptime(dtg[-5:], "%H:%M")
            timedisplay = datetime.datetime.strftime(timepredisplay, "%H:%M %p")
            subtypedisplay = subtype.upper()

            if subtype in ['cardio', 'sport', 'gym']: #if exercise
                printstring = f'''{timedisplay} - {subtypedisplay}
{title}
{description}
Calories: {calorie}'''
                calout += calorie
            else: #if meal
                costdisplay = str(cost/100)
                printstring = f'''{timedisplay} - {subtypedisplay}
{title}
{description}
Calories: {calorie}
${costdisplay}'''
                c1, p1, f1 = get_mac_from_desc(description)
                c += c1
                p += p1
                f += f1
                calin += calorie
                money += cost/100
            printstring += '\n'
            if display: #only if function is called to display (user wants to see activitylog)
                finalstring += printstring #add printstring for each activity into finalstring


        if display: #return printstring to viewlog tele function
            return finalstring
        else: #return total macros to log macros function
            return calin, calout, c, p, f, money
    else:
        if display: #return printstring to viewlog tele function
            return 'no activities today :/'
        else: #return zeros to log macros function
            calout = get_defaults(username, 'calout')
            return 0,calout,0,0,0,0











print(username_validation('matthanfoo', '12901937'))
##print(userid_exists('12901937'))
##print(usermacros_created('12901937'))
##print(usermacros_created('12901937'))
##print(sql_set_defaultmacro('calout', 2810, '12901937'))
##print(display_macros('matthanfoo'))
##print(log_macros('matthanfoo'))
##print(get_defaults('matthanfoo', 'calout'))
##print(fetch_today_activity('matthanfoo'))
##print(display_activity_log('matthanfoo', True))
