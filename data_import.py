import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import database as db
import queries as q
import cache as cc


def fetch_credits():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('resources/token.json'):
        creds = Credentials.from_authorized_user_file('resources/token.json', scope)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:  # Create token.json in first time setup
            flow = InstalledAppFlow.from_client_secrets_file('resources/credentials.json', scope)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('resources/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
rl_doc = '1zjW4_TEsyd4yDSsVuZsrUritfwHgHZQ3e0t9GnWXrKA'
creds = fetch_credits()
service = build('sheets', 'v4', credentials=creds)


def new_data_available() -> bool:
    total = cc.data.get('TOTAL_GAMES')
    result = service.spreadsheets().values().get(spreadsheetId=rl_doc, range=f'Games!A{total + 1}:W').execute()
    game_data = result.get('values', [])
    return game_data and int(game_data[0][0]) > total and all(game_data[0]) and len(game_data[0]) == 23


def insert_new_data():
    total = q.total_games()
    result = service.spreadsheets().values().get(spreadsheetId=rl_doc, range=f'Games!A{total + 1}:W').execute()
    game_data = result.get('values', [])

    # Insert if data does not match, assert that not data point is missing
    for game in game_data:
        q.insert_game_data(game)


# Reads the provided .csv data from the resources folder and creates or overwrites 'test.db' in the resources folder.
def import_from_local_file():
    conn = db.connect_to_database()
    c = conn.cursor()

    # Drop tables
    try:
        c.execute("DROP TABLE games")
        c.execute("DROP TABLE scores")
    except sqlite3.Error as e:
        print(e)

    # Create them anew
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                gameID INTEGER,
                playerID INTEGER,
                rank TEXT NOT NULL CHECK(rank IN ('',' ','GC','D1','D2','D3','C1','C2','C3','GC1','GC2','GC3','SSL')),
                score INTEGER NOT NULL CHECK(score>=0),
                goals INTEGER NOT NULL CHECK(goals>=0),
                assists INTEGER NOT NULL CHECK(assists>=0),
                saves INTEGER NOT NULL CHECK(saves>=0),
                shots INTEGER NOT NULL CHECK(shots>=0),
                PRIMARY KEY(gameID,playerID)
            );       
            """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS games (
                gameID INTEGER PRIMARY KEY,
                date TEXT NOT NULL CHECK(date IS strftime('%Y-%m-%d', date)),
                goals INTEGER NOT NULL CHECK(goals>=0),
                against INTEGER NOT NULL CHECK(against>=0)
            ); 
            """)
        conn.commit()
    except sqlite3.Error as e:
        print(e)

    # Add data from .csv
    with open(f'resources/{name}') as stats:
        for line in stats:
            data = line.split(',')
            games_data = [data[0], data.pop(1), data.pop(1), data.pop(1)]
            c.execute("INSERT INTO games VALUES(?,?,?,?)", games_data)
            knus = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
            puad = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
            sticker = [data[0], data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1), data.pop(1)]
            c.execute("INSERT INTO scores VALUES(?,0,?,?,?,?,?,?)", knus)
            c.execute("INSERT INTO scores VALUES(?,1,?,?,?,?,?,?)", puad)
            c.execute("INSERT INTO scores VALUES(?,2,?,?,?,?,?,?)", sticker)
    c.close()
    conn.commit()
