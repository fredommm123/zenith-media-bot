import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id]
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0")) if os.getenv("ADMIN_CHAT_ID") else None  # ID чата для админов

# Payment settings
MIN_WITHDRAWAL = int(os.getenv("MIN_WITHDRAWAL", "100"))
REFERRAL_PERCENT = int(os.getenv("REFERRAL_PERCENT", "10"))

# Crypto Pay settings
CRYPTO_PAY_TOKEN = "470393:AAG7PA6bmGHxmXcpLbku4zM9gEtP1yGb8FU"
CRYPTO_PAY_TESTNET = False  # False для основной сети, True для тестнета

# Withdrawal rates (views per 1 RUB)
TIKTOK_RATE_PER_1000_VIEWS = 65  # 65 рублей за 1000 просмотров TikTok
DEFAULT_YOUTUBE_RATE_PER_1000_VIEWS = 50  # 50 рублей за 1000 просмотров YouTube (по умолчанию)

# Database
DATABASE_PATH = "bot_database.db"

# TikTok Parser
TIKTOK_PARSER_TEST_MODE = os.getenv("TIKTOK_PARSER_TEST_MODE", "false").lower() == "true"
