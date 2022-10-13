from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import queries

scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
rl_doc = '1zjW4_TEsyd4yDSsVuZsrUritfwHgHZQ3e0t9GnWXrKA'


def fetch_from_sheets():
    # Latest game on website
    latest_id = queries.max_id()

    # Google API
    credentials = Credentials.from_authorized_user_file('../resources/token.json', scope)
    service = build('sheets', 'v4', credentials=credentials)
    result = service.spreadsheets().values().get(spreadsheetId=rl_doc, range=f'Games!A{latest_id + 1}:W').execute()
    game_data = result.get('values', [])

    # Insert if data does not match
    if game_data:
        for game in game_data:
            if all(game):
                queries.insert_game_data(game)
