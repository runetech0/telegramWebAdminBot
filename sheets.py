import os
from Google import Create_Service

FOLDER_PATH = '/home/virchual/python/telegramBots/telegramWebAdminBot'
CLIENT_SECRET_FILE = os.path.join(FOLDER_PATH, 'Client_Secret.json')
API_SERVICE_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

service = Create_Service(
    CLIENT_SECRET_FILE, API_SERVICE_NAME, API_VERSION, SCOPES)

spreadsheetId = "1DJ-mS1aMl5FR9xFT4C5iQxTzg6v_7DWEMKwq9LmgZhs"


def create_spread_sheet():
    spreadsheet = {
        'properties': {
            'title': 'Sheet 1'
        }
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
    return spreadsheet


def update_values(spreadsheet_id, range_name, value_input_option,
                  _values):
    # [START sheets_update_values]
    values = [
        [
            # Cell values ...
        ],
        # Additional rows ...
    ]
    # [START_EXCLUDE silent]
    values = _values
    # [END_EXCLUDE]
    body = {
        'values': values
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption=value_input_option, body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))
    # [END sheets_update_values]
    return result


rangeName = 'A1'
valueInputOption = 'USER_ENTERED'
values = [
    ['Col 1', 'Col 2', 'Col 3', 'Col 4'],
    ['Row 2']
]

update_values(spreadsheetId, rangeName, valueInputOption, values)
