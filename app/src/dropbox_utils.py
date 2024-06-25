import dropbox
import os
from src import log_utils

log = log_utils.get_logger()

PAUSE_EXECUTION_PATH = '/pokemon-shuffle/pause_execution.txt'
PAUSE_SLEEP_PATH = '/pokemon-shuffle/pause_sleep.txt'
NEXT_AWAKE_TIME_PATH = '/pokemon-shuffle/next_awake_time.txt'


DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_TOKEN")
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

dbx = None

def get_dbx_connection():
    global dbx
    try:
        if dbx is None or not is_token_valid():
            dbx = refresh_access_token()
        return dbx
    except:
        dbx = refresh_access_token()
        return dbx


def is_token_valid():
    try:
        dbx.users_get_current_account()
        return True
    except dropbox.exceptions.AuthError:
        return False

def refresh_access_token():
    oauth2_access_token = dropbox.Dropbox(
        app_key=APP_KEY,
        app_secret=APP_SECRET,
        oauth2_refresh_token=REFRESH_TOKEN
    )

    return oauth2_access_token

def read_file_from_dropbox(file_path):
    try:
        dbx = get_dbx_connection()
        metadata, response = dbx.files_download(file_path)
        content = response.content.decode('utf-8')
        return content
    except dropbox.exceptions.ApiError as e:
        log.debug(f"Error reading file from Dropbox: {e}")
        return None

def clear_file_in_dropbox(file_path):
    try:
        dbx = get_dbx_connection()
        dbx.files_upload(b"", file_path, mode=dropbox.files.WriteMode("overwrite"))
        log.debug("File cleared successfully.")
    except dropbox.exceptions.ApiError as e:
        log.debug(f"Error clearing file in Dropbox: {e}")

def update_file_with_new_content(file_path, new_content):
    try:
        dbx = get_dbx_connection()
        dbx.files_upload(new_content.encode(), file_path, mode=dropbox.files.WriteMode("overwrite"))
        log.debug("File updated successfully.")
    except dropbox.exceptions.DropboxException as e:
        log.debug(f"Error updating file in Dropbox: {e}")