# gpt/skills/email_manager.py

import os
import base64
import pickle
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from gpt.skill_registry import skill

# Graceful import for Google libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    # Define dummy classes so the rest of the file can be parsed
    class Request: pass
    class Credentials: pass
    class InstalledAppFlow: pass
    def build(*args, **kwargs): return None

# --- Gmail API Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
]
TOKEN_PATH = 'token.pickle'
CREDENTIALS_PATH = 'credentials.json'

class GmailManager:
    """Handles all interactions with the Gmail API."""
    def __init__(self, token_path=TOKEN_PATH, credentials_path=CREDENTIALS_PATH):
        if not GOOGLE_LIBS_AVAILABLE:
            self.service = None
            return

        self.token_path = token_path
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None

    def authenticate(self):
        """Authenticate user, or return False if not possible."""
        if not GOOGLE_LIBS_AVAILABLE: return False

        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Failed to refresh token: {e}")
                    return self._run_oauth_flow()
            else:
                return self._run_oauth_flow()

        if self.creds:
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            self.service = build('gmail', 'v1', credentials=self.creds)
            return True
        return False

    def _run_oauth_flow(self):
        """Runs the OAuth flow to get new credentials."""
        if not os.path.exists(self.credentials_path):
            print(f"Warning: '{self.credentials_path}' not found for Gmail auth.")
            return False
        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
            self.creds = flow.run_local_server(port=0)
            return True
        except Exception as e:
            print(f"OAuth flow failed: {e}")
            return False

    def send_email(self, to: str, subject: str, body: str, **kwargs):
        """Create and send an email message."""
        if not self.service and not self.authenticate():
            return "Gmail authentication failed or is required."

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            sent = self.service.users().messages().send(userId='me', body={'raw': raw}).execute()
            return f"Email sent to {to} with ID: {sent['id']}"
        except Exception as e:
            return f"Failed to send email: {e}"

    def search_emails(self, query: str, max_results: int = 5):
        """Search emails and return a summary of the results."""
        if not self.service and not self.authenticate():
            return "Gmail authentication failed or is required."

        try:
            response = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = response.get('messages', [])
            if not messages:
                return f"No emails found matching '{query}'."

            summaries = []
            for msg_info in messages:
                msg = self.service.users().messages().get(userId='me', id=msg_info['id'], format='metadata', metadataHeaders=['From', 'Subject']).execute()
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                summaries.append(f"From: {sender}\nSubject: {subject}\nSnippet: {msg['snippet']}")

            return "\n\n---\n\n".join(summaries)
        except Exception as e:
            return f"Failed to search emails: {e}"

# --- Skill Definitions ---

gmail_manager = GmailManager()

@skill(
    patterns=[
        r"send an email to (?P<to>.+) with subject (?P<subject>.+) and body (?P<body>.+)",
        r"email (?P<to>.+) with subject (?P<subject>.+) that says (?P<body>.+)"
    ],
    description="Sends an email using your Gmail account."
)
def send_email_skill(to: str, subject: str, body: str) -> str:
    if not GOOGLE_LIBS_AVAILABLE:
        return "Email skill is not available (Google client libraries are missing)."
    try:
        return gmail_manager.send_email(to=to.strip(), subject=subject.strip(), body=body.strip())
    except Exception as e:
        return f"Error sending email: {e}"

@skill(
    patterns=[
        r"search for emails from (?P<query>.+)",
        r"find emails about (?P<query>.+)"
    ],
    description="Searches for emails in your Gmail account."
)
def search_emails_skill(query: str) -> str:
    if not GOOGLE_LIBS_AVAILABLE:
        return "Email skill is not available (Google client libraries are missing)."
    try:
        search_query = f"from:{query.strip()}" if "from" in query.lower() else query
        return gmail_manager.search_emails(query=search_query)
    except Exception as e:
        return f"Error searching emails: {e}"

@skill(
    patterns=[r"check my unread emails", r"any new emails"],
    description="Checks for new (unread) emails."
)
def check_unread_emails_skill() -> str:
    if not GOOGLE_LIBS_AVAILABLE:
        return "Email skill is not available (Google client libraries are missing)."
    try:
        return gmail_manager.search_emails(query="is:unread", max_results=5)
    except Exception as e:
        return f"Error checking unread emails: {e}"