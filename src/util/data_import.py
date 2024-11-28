import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def fetch_credits():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scope)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:  # Create token.json in first time setup
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scope)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


scope = ['https://www.googleapis.com/auth/spreadsheets.readonly']
RL_DOC = '1zjW4_TEsyd4yDSsVuZsrUritfwHgHZQ3e0t9GnWXrKA'
creds = fetch_credits()
service = build("sheets", "v4", credentials=creds)


def is_new_data_available(latest_game_id_excel: int) -> bool:
    result = service.spreadsheets().values().get(spreadsheetId=RL_DOC, range=f"Games!A{latest_game_id_excel + 1}:W").execute()
    game_data = result.get("values", [])
    return game_data and int(game_data[0][0]) > latest_game_id_excel and all(game_data[0]) and len(game_data[0]) == 23


def insert_new_data(dashboard) -> None:
    result = service.spreadsheets().values().get(spreadsheetId=RL_DOC, range=f"Games!A{dashboard.q.total_games() + 1}:W").execute()
    game_data = result.get("values", [])

    # Insert if data does not match, assert that not data point is missing
    for game in game_data:
        dashboard.q.insert_game_data(game)
