import os
import base64
import pickle
from typing import List, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Scopes required for Gmail full access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
]

class GmailManager:
    def __init__(self, token_path='token.pickle', credentials_path='credentials.json'):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None

    def authenticate(self):
        """Authenticate user with OAuth2, caching the token for reuse."""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
        # If token is invalid or doesn't exist, start flow
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)

    def send_email(self, to: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        """Create and send an email message."""
        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = ", ".join(cc)
        if bcc:
            message['bcc'] = ", ".join(bcc)
        message.attach(MIMEText(body, 'plain'))
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_obj = {'raw': raw}
        try:
            sent = self.service.users().messages().send(userId='me', body=message_obj).execute()
            return f"Email sent! ID: {sent['id']}"
        except Exception as e:
            return f"Failed to send email: {e}"

    def list_messages(self, query: Optional[str] = None, max_results: int = 10):
        """List message IDs matching query."""
        response = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = response.get('messages', [])
        return messages

    def get_message(self, msg_id: str):
        """Get full message content."""
        msg = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        snippet = msg.get('snippet', '')

        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        from_ = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        # Extract plain text parts - simplified
        parts = payload.get('parts', [])
        body = ""
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        return {'subject': subject, 'from': from_, 'snippet': snippet, 'body': body}

    def search_messages(self, query: str, max_results: int = 5):
        """Search emails matching query, return list of summaries."""
        messages = self.list_messages(query=query, max_results=max_results)
        result = []
        for msg in messages:
            full_msg = self.get_message(msg['id'])
            result.append(full_msg)
        return result

    def delete_message(self, msg_id: str):
        """Move message to trash."""
        try:
            self.service.users().messages().trash(userId='me', id=msg_id).execute()
            return f"Message {msg_id} moved to trash."
        except Exception as e:
            return f"Failed to delete message: {e}"

    def summarize_message(self, msg_id: str):
        """Return a brief summary of the email body, or snippet."""
        msg = self.get_message(msg_id)
        # For demo: return snippet; in practice, call an NLP summarizer
        return msg.get('snippet', '') or (msg.get('body')[:150] + "...")

