import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8512645298:AAGAQhbbCXNVsN8JHvoXkoahtVb2gBE9q-c")
OWNER_ID = int(os.environ.get("OWNER_ID", "5089821980"))
BASE_URL = os.environ.get("BASE_URL", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "my-super-secret-key-change-this-1234")
FILES_DIR = "./files"
