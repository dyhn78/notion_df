from __future__ import print_function

import os.path
from abc import ABCMeta

# noinspection PyPackageRequirements
import googleapiclient
# noinspection PyPackageRequirements
from google.auth.transport.requests import Request
# noinspection PyPackageRequirements
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
# noinspection PyPackageRequirements
from googleapiclient.discovery import build
# noinspection PyPackageRequirements
from googleapiclient.errors import HttpError

from notion_zap.cli.core.mixins import Executable, ValueCarrier

# If modifying these scopes, delete the file token.json.
#  https://developers.google.com/calendar/api/guides/auth
SCOPES = ['https://www.googleapis.com/auth/calendar']

PATH_CREDENTIALS = os.path.join(os.path.dirname(__file__), 'credentials.json')
PATH_TOKEN = os.path.join(os.path.dirname(__file__), 'token.json')


def open_gcal_service() -> googleapiclient.discovery.Resource:
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(PATH_TOKEN):
        creds = Credentials.from_authorized_user_file(PATH_TOKEN, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                PATH_CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(PATH_TOKEN, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


class GcalManagerAbs(ValueCarrier, Executable, metaclass=ABCMeta):
    api_response_error = HttpError

    def __init__(self):
        self.service = open_gcal_service()

    def __bool__(self):
        return True


if __name__ == '__main__':
    open_gcal_service()
