import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def authenticate_gmail():
    """Shows basic usage of the Gmail API. Lists the user's Gmail labels."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def download_pdf_attachments(service, query):
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    if not messages:
        print("No messages found.")
        return

    for msg in messages:
        msg_id = msg['id']
        message = service.users().messages().get(userId='me', id=msg_id).execute()

        for part in message['payload']['parts']:
            if part['filename'] and 'pdf' in part['filename']:
                if 'data' in part['body']:
                    data = part['body']['data']
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                elif 'attachmentId' in part['body']:
                    att_id = part['body']['attachmentId']
                    attachment = service.users().messages().attachments().get(userId='me', messageId=msg_id,
                                                                              id=att_id).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                if 'indianoil' in part['filename'].lower():
                    continue
                path = os.path.join('downloads', part['filename'])
                with open(path, 'wb') as f:
                    f.write(file_data)
                print(f"Downloaded {part['filename']} to {path}")


if __name__ == '__main__':
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)

    # Example query to search for bank statement emails
    start_date = '2018/01/01'
    end_date = '2014/09/09'

    query = f'from:hdfcbanksmartstatement@hdfcbank.net has:attachment after:{start_date} before:{end_date}'

    download_pdf_attachments(service, query)
