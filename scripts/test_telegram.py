import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Settings
from modules.notifications.telegram_bot import TelegramBot

if __name__ == "__main__":
    print("Telegram configured:", TelegramBot(Settings.load()).configured)
