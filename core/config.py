import os
from dotenv import load_dotenv

load_dotenv()

# Bot settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "").split(",") if admin_id]
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0")) if os.getenv("ADMIN_CHAT_ID") else None  # ID чата для админов

# Payment settings
MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", "30"))  # Минимальная сумма вывода в рублях
REFERRAL_PERCENT = int(os.getenv("REFERRAL_PERCENT", "10"))

# Crypto Pay settings
CRYPTO_PAY_TOKEN = os.getenv("CRYPTO_PAY_TOKEN")
CRYPTO_PAY_TESTNET = os.getenv("CRYPTO_PAY_TESTNET", "false").lower() == "true"

# Withdrawal rates
TIKTOK_RATE_PER_1000_VIEWS = 65  # 65 рублей за 1000 просмотров TikTok (фиксированная ставка)
# YouTube: ставку устанавливает администратор индивидуально для каждого канала

# Database
DATABASE_PATH = "bot_database.db"

# TikTok Parser
TIKTOK_PARSER_TEST_MODE = os.getenv("TIKTOK_PARSER_TEST_MODE", "false").lower() == "true"
