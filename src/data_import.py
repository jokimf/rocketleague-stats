import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import cache as cc
import queries as q


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
