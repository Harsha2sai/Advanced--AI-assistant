import os
import base64
import json
import typing # Added for typing.cast
from typing import List, Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import logging
import time
import binascii # Added for base64 decode error handling
import html # Added for HTML entity decoding
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.http import BatchHttpRequest

# Scopes required for Gmail full access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
]

class GmailManager:
    def __init__(self, token_path='token.json', credentials_path='credentials.json'):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self.creds: Any = None # Changed type hint to Any to resolve Pylance error with Credentials type
        self.service: Any = None # Use Any due to dynamic nature of googleapiclient.discovery.build output

    def authenticate(self):
        """Authenticate user with OAuth2, caching the token for reuse.
        
        Note: This class previously used 'token.pickle' for storing credentials.
        It now uses 'token.json'. Existing 'token.pickle' files will be automatically
        migrated to 'token.json' on first authentication.
        """
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'r') as token:
                    json_data = json.load(token)
                    self.creds = Credentials.from_authorized_user_info(json_data, SCOPES)
        except Exception as e:
            # Attempt to load from token.pickle for backward compatibility if token.json fails
            if self.token_path == 'token.json' and os.path.exists('token.pickle'):
                logging.warning(f"Failed to load token from {self.token_path}. Attempting to load from 'token.pickle' for backward compatibility.")
                try:
                    with open('token.pickle', 'r') as token_pickle:
                        json_data = json.load(token_pickle)
                        self.creds = Credentials.from_authorized_user_info(json_data, SCOPES)
                    # If successful, save to new token.json path
                    with open(self.token_path, 'w') as token_json:
                        token_json.write(self.creds.to_json())
                    logging.info(f"Successfully migrated credentials from 'token.pickle' to '{self.token_path}'.")
                except Exception as e_pickle:
                    raise RuntimeError(f"Failed to load token from 'token.pickle' either: {e_pickle}. Original error: {e}")
            else:
                raise RuntimeError(f"Failed to load token from {self.token_path}: {e}")
        
        # If token is invalid or doesn't exist, start flow
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    raise RuntimeError(f"Failed to refresh token: {e}")
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    raise RuntimeError(f"OAuth flow failed: {e}")
            try:
                with open(self.token_path, 'w') as token:
                    if self.creds is None:
                        logging.error("Authentication failed: Credentials are missing after OAuth flow.")
                        raise RuntimeError("Missing credentials after successful OAuth flow.")
                    # Use typing.cast to assert that self.creds is not None for the type checker
                    creds_to_save = typing.cast(Credentials, self.creds)
                    token.write(creds_to_save.to_json())
            except Exception as e:
                raise RuntimeError(f"Failed to save token to {self.token_path}: {e}")

        try:
            self.service = build('gmail', 'v1', credentials=self.creds)
        except Exception as e:
            raise RuntimeError(f"Failed to build Gmail service: {e}")

    def _ensure_authenticated(self):
        """Raises an error if the Gmail service is not authenticated."""
        if self.service is None:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

    def send_email(self, to: str, subject: str, body: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        """Create and send an email message."""
        self._ensure_authenticated()
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
        self._ensure_authenticated()
        
        retries = 0
        max_retries = 3
        base_delay = 1 # seconds

        while retries <= max_retries:
            try:
                response = self.service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
                messages = response.get('messages', [])
                return messages
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504] and retries < max_retries:
                    delay = base_delay * (2 ** retries)
                    logging.warning(f"Gmail API HttpError (status: {e.resp.status}) encountered. Retrying in {delay} seconds... (Attempt {retries + 1}/{max_retries})")
                    time.sleep(delay)
                    retries += 1
                else:
                    logging.error(f"Gmail API HttpError: {e}")
                    return []
            except Exception as e:
                logging.error(f"An unexpected error occurred while listing messages: {e}")
                return []
        return [] # Should not be reached if max_retries is handled correctly, but as a fallback

    def _html_to_plain_text(self, html_content: str) -> str:
        """Converts HTML content to plain text by stripping tags and decoding HTML entities."""
        import re
        # Basic regex to strip HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities using html.unescape for robust decoding
        text = html.unescape(text)
        return text.strip()

    def get_message(self, msg_id: str):
        """Get full message content with improved error handling and body extraction."""
        self._ensure_authenticated()
        try:
            msg = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        except HttpError as e:
            logging.error(f"Gmail API HttpError while fetching message {msg_id}: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching message {msg_id}: {e}")
            return None

        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        snippet = msg.get('snippet', '')

        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        from_ = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')

        body_plain = ""
        body_html = ""

        def decode_data(data):
            try:
                return base64.urlsafe_b64decode(data).decode('utf-8')
            except Exception as e:
                logging.warning(f"Failed to base64 decode part data: {e}")
                return ""

        # Handle single-part messages
        if 'body' in payload and payload['body'].get('data'):
            data = payload['body']['data']
            decoded_content = decode_data(data)
            if payload.get('mimeType') == 'text/plain':
                body_plain = decoded_content
            elif payload.get('mimeType') == 'text/html':
                body_html = decoded_content

        # Handle multi-part messages
        parts = payload.get('parts', [])
        for part in parts:
            mime_type = part.get('mimeType')
            data = part['body'].get('data') if 'body' in part else None

            if data:
                decoded_content = decode_data(data)
                if mime_type == 'text/plain':
                    body_plain += decoded_content
                elif mime_type == 'text/html':
                    body_html += decoded_content
            elif mime_type == 'multipart/alternative':
                for sub_part in part.get('parts', []):
                    sub_mime_type = sub_part.get('mimeType')
                    sub_data = sub_part['body'].get('data') if 'body' in sub_part else None
                    if sub_data:
                        decoded_content = decode_data(sub_data)
                        if sub_mime_type == 'text/plain':
                            body_plain += decoded_content
                        elif sub_mime_type == 'text/html':
                            body_html += decoded_content

        final_body = body_plain.strip()
        if not final_body and body_html:
            final_body = self._html_to_plain_text(body_html).strip()

        return {'subject': subject, 'from': from_, 'snippet': snippet, 'body': final_body}

    def search_messages(self, query: str, max_results: int = 5):
        """Search emails matching query, return list of summaries using batch requests."""
        self._ensure_authenticated()

        messages = self.list_messages(query=query, max_results=max_results)
        if not messages:
            return []

        result_map = {}
        errors = []

        def callback(request_id, response, exception):
            if exception is not None:
                errors.append(f"Error fetching message {request_id}: {exception}")
                print(f"Error fetching message {request_id}: {exception}") # Log the error
            else:
                payload = response.get('payload', {})
                headers = payload.get('headers', [])
                snippet = response.get('snippet', '')

                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
                from_ = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                
                body = ""
                parts = payload.get('parts', [])
                if parts: # Handle multipart messages
                    for part in parts:
                        if part['mimeType'] == 'text/plain':
                            data = part['body'].get('data')
                            if data:
                                try:
                                    body += base64.urlsafe_b64decode(data).decode('utf-8')
                                except (binascii.Error, ValueError, UnicodeDecodeError) as decode_error:
                                    logging.warning(f"Failed to decode base64 for message {request_id}, part text/plain: {decode_error}")
                        elif part['mimeType'] == 'multipart/alternative':
                            for sub_part in part.get('parts', []):
                                if sub_part['mimeType'] == 'text/plain':
                                    sub_data = sub_part['body'].get('data')
                                    if sub_data:
                                        try:
                                            body += base64.urlsafe_b64decode(sub_data).decode('utf-8')
                                        except (binascii.Error, ValueError, UnicodeDecodeError) as decode_error:
                                            logging.warning(f"Failed to decode base64 for message {request_id}, sub-part text/plain: {decode_error}")
                else: # Handle single part messages
                    data = payload['body'].get('data')
                    if data:
                        try:
                            body += base64.urlsafe_b64decode(data).decode('utf-8')
                        except (binascii.Error, ValueError, UnicodeDecodeError) as decode_error:
                            logging.warning(f"Failed to decode base64 for message {request_id}, single part: {decode_error}")

                result_map[request_id] = {
                    'subject': subject,
                    'from': from_,
                    'snippet': snippet,
                    'body': body
                }

        batch = self.service.new_batch_http_request()
        for msg in messages:
            batch.add(self.service.users().messages().get(userId='me', id=msg['id'], format='full'),
                      callback=callback, request_id=msg['id'])
        batch.execute()

        # Collect results in the order of original messages and respect max_results
        final_results = []
        for msg in messages:
            if msg['id'] in result_map:
                final_results.append(result_map[msg['id']])
            if len(final_results) >= max_results:
                break
        
        if errors:
            print(f"Encountered errors during batch message fetching: {errors}")

        return final_results

    def delete_message(self, msg_id: str):
        """Move message to trash."""
        self._ensure_authenticated()
        try:
            self.service.users().messages().trash(userId='me', id=msg_id).execute()
            return f"Message {msg_id} moved to trash."
        except Exception as e:
            return f"Failed to delete message: {e}"

    def summarize_message(self, msg_id: str):
        """Return a brief summary of the email body, or snippet."""
        self._ensure_authenticated()
        message_content = self.get_message(msg_id)
        if message_content is None:
            return "Could not retrieve message for summarization."
        
        snippet = message_content.get('snippet', '')
        body = message_content.get('body', '')
        
        # For demo: return snippet; in practice, call an NLP summarizer
        return snippet or (body[:150] + "...") if body else ""
