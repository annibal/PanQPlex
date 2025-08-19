import os, pickle
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CONF = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config")) / "n2bl"
CONF.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = CONF / "token.pickle"
CLIENT_SECRETS_FILE = CONF / "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube"]

def get_credentials():
    creds = None
    if TOKEN_FILE.exists():
        with TOKEN_FILE.open("rb") as f: creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        with TOKEN_FILE.open("wb") as f: pickle.dump(creds, f)
    return creds

def get_youtube_service():
    return build("youtube", "v3", credentials=get_credentials())
