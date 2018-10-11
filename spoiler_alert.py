import argparse
import datetime
import json
import mechanicalsoup as msoup
import smtplib
import time


import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

from getpass import getpass

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

month_to_num = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

def get_input():
    '''
    Gets the list of email id and the associated TV series preferences and stores it
    in a database.
    '''
    while True:
        email_id = input("Email address: ").strip()
        if email_id == "":
            break
        tv_series = input("TV Series: ").strip()

        populate_db(email_id, tv_series)

def populate_db(email_id, tv_series):
    '''
    Populates the database with a new entry.

    :param email_id: Email id of the client
    :param tv_series: A string storing the TV series preferences for the client
    '''

    sql_formula = "INSERT INTO PREFS (email, series) VALUES (%s, %s)"
    cur, db = setup_db()
    entry = (email_id, tv_series)
    cur.execute(sql_formula, entry)
    db.commit()
    cur.close()
    db.close()

def setup_db():
    '''
    Sets up the MySQL database.
    '''
    login_file = open("db_login.json")
    login_info = json.loads(login_file.read())
    db = MySQLdb.connect(**login_info)
    cursor = db.cursor()
    add_database(cursor)
    add_table(cursor)
    return cursor, db

def add_database(cursor):
    '''
    Connects a database named "TV_PREFS" or creates it first if it does
    not exist.

    :param cursor: MySQLdb connect cursor
    '''
    cursor.execute("SHOW DATABASES")
    for db in cursor:
        if "TV_PREFS" in db:
            cursor.execute("USE TV_PREFS")
            break
    else:
        cursor.execute("CREATE DATABASE TV_PREFS")
        cursor.execute("USE TV_PREFS")

def add_table(cursor):
    '''
    Creates a table named "PREFS" if it does not exist in the database.

    :param cursor: MySQLdb connect cursor
    '''
    cursor.execute("SHOW TABLES")
    for tb in cursor:
        if "PREFS" in tb:
            break
    else:
        cursor.execute("CREATE TABLE PREFS (email VARCHAR(255), series TEXT)")

def send_alerts():
    '''
    Send spoiler alerts to all the clients about their TV series preferences
    stored in the database.
    '''

    cur, db = setup_db()
    cur.execute("SELECT * FROM PREFS")
    result = cur.fetchall()
    cur.close()
    db.close()

    server, sender_email_id = setup_server()

    for email, tv_prefs in result:
        send_email(server, sender_email_id, email, tv_prefs)

    server.quit()

def send_email(server, sender_email_id, client_email_id, tv_prefs):
    '''
    Sends email with spoiler alert to a client about their TV series preferences.

    :param server: SMTP object
    :param sender_email_id: Email id of the sender
    :param client_email_id: Email id of the client
    :param tv_prefs: String storing the TV series preferences of the client
    '''
    message = create_msg_content(sender_email_id, client_email_id, tv_prefs)
    server.sendmail(sender_email_id, client_email_id, message)

def setup_server():
    '''
    Sets up an SMTP server.

    Returns: SMTP object and sender's email id
    '''
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    sender_email_id = login_user(server)

    return server, sender_email_id

def try_until_success(func):
    '''
    Function decorator to repeatedly call func for a max of 5 times
    in case of smtplib.SMTPAuthenticationError
    '''

    def wrapper(*args, **kwargs):
        for i in range(5):
            try:
                return func(*args, **kwargs)
            except smtplib.SMTPAuthenticationError:
                print("Incorrect email-id/password entered.")
        raise smtplib.SMTPAuthenticationError
    return wrapper

@try_until_success
def login_user(server):
    '''
    Asks the user for email id / password and logs in the server

    :param server: smtplib.SMTP object

    Returns: The email id entered by the user
    '''

    sender_email_id = input("Enter the sender's email id: ").strip()
    sender_pwd = getpass()
    server.login(sender_email_id, sender_pwd)
    return sender_email_id

def create_msg_content(sender_email_id, client_email_id, tv_prefs):
    '''
    Constructs an appropriate email using the search query and the
    results present in results_df

    :param sender_email_id: Email id of the sender
    :param client_email_id: Email id of the client
    :param tv_prefs: String storing the TV series preferences of the client

    Returns: The email msg as a string
    '''

    message = MIMEMultipart()
    message['From'] = sender_email_id
    message['To'] = client_email_id
    message['Subject'] = 'Spoiler alerts!'

    body = create_msg_body(tv_prefs)

    message.attach(MIMEText(body, 'plain'))

    return message.as_string()
    
def create_msg_body(tv_prefs):
    '''
    Creates the email's message body.

    :param tv_prefs: String storing the TV series preferences of the client

    Returns: The email's message body as a string
    '''

    body = ""
    for name in tv_prefs.split(','):
        body = body + create_series_info(name) + '\n'
    return body 
    
def create_series_info(name):
    '''
    Creates the message information about a TV series.

    :param name: Name of the TV series

    Returns: The TV series' message information
    '''

    line_1 = "TV series name: " + name
    line_2 = "Status: " + get_latest_air_info(name)

    return line_1 + '\n' + line_2 + '\n'
    
def get_latest_air_info(name):
  '''
  Gives information about the latest air date of a TV series from IMDB 

  :param name: Name of the TV series

  Returns: String storing the latest air info
  '''
  
  latest_season_dates = get_latest_season_dates(name, level=0)

  for idx, date in enumerate(latest_season_dates):
    if type(date) == datetime.datetime:
      if datetime.datetime.today() < date:
        if idx==0:
          return "The next season begins " + str(date)[:str(date).find(' ')]
        else:
          return "The next episode airs on " + str(date)[:str(date).find(' ')]
    else:
      if idx==0:
        return "The next season begins " + str(date)
      else:
        return "The next episode airs in " + str(date)

  return "The show has finished streaming all its episodes"

def get_latest_season_dates(name, level=0):
  '''
  Gets the air dates of episodes of the latest season of a TV show from IMDB

  :param name: Name of the TV show
  :param level: Integer indicating levels of lateness. Higher number denotes earlier season. Latest season is denoted by 0.

  Returns: List of datetime.datetime objects storing the air dates of episodes
  '''
  browser = msoup.StatefulBrowser()
  browser.open("https://www.imdb.com/")

  time.sleep(2)

  browser.select_form()
  browser["q"] = name
  response = browser.submit_selected()

  next = browser.get_current_page()
  result_list = next.find_all("tr", class_="findResult odd")
  series_home = browser.open("https://www.imdb.com/"+result_list[0].find_all('a', href=True)[0]['href'])

  time.sleep(2)

  series_home = browser.get_current_page()
  series_home.find_all(id='title-episode-widget')
  seasons_box = series_home.find_all(id='title-episode-widget')
  browser.open('https://www.imdb.com/'+seasons_box[0].find_all('a', href=True)[level]['href'])

  time.sleep(2)

  latest_season = browser.get_current_page()
  all_dates_div = latest_season.find_all("div", class_='airdate')
  all_dates = [date_div.string.strip() for date_div in all_dates_div]

  for idx, date in enumerate(all_dates):
    date = date.replace('.', '')
    if len(date) == 11 or len(date) == 10:
      all_dates[idx] = to_datetime(date)

  return all_dates

def to_datetime(date):
  '''
  Converts the date to a datetime.datetime object

  :param data: String representing date

  Returns: The equivalent datetime.datetime object
  '''
  year = int(date[-4:])
  month = int(month_to_num[date[date.find(' ')+1 : date.find(' ')+4]])
  day = int(date[:date.find(' ')])

  return datetime.datetime(year, month, day)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spoiler alert system")
    parser.add_argument('-u', '--update', action='store_true', 
                        help='Add new entry(/ies) to the database')
    parser.add_argument('-a', '--alert', action='store_true',
                        help='Send email alerts')
    args = parser.parse_args()
    if args.update:
        get_input()
    if args.alert:
        send_alerts()
