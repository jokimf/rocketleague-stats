from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

import queries as q
import random_facts as r

scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
rl_doc = '1zjW4_TEsyd4yDSsVuZsrUritfwHgHZQ3e0t9GnWXrKA'


def fetch_from_sheets():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('../resources/token.json'):
        creds = Credentials.from_authorized_user_file('../resources/token.json', scope)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print('invalid')
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../resources/credentials.json', scope)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../resources/token.json', 'w') as token:
            token.write(creds.to_json())

    # Latest game on website
    latest_id = q.max_id()

    # Google API
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=rl_doc, range=f'Games!A{latest_id + 1}:W').execute()
    game_data = result.get('values', [])

    # Insert if data does not match
    if game_data:
        for game in game_data:
            if all(game):
                q.insert_game_data(game)

        # Calculate costly stuff in advance
        r.random_facts = r.generate_random_facts()


if __name__ == '__main__':
    fetch_from_sheets()
