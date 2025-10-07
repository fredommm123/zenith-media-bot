from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import Database
from utils import format_currency
import config

router = Router()
db = Database(config.DATABASE_PATH)


@router.message(F.text == " Вывод средств")
async def withdrawal_disabled(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(" Вы не зарегистрированы! Используйте /start", parse_mode="HTML")
        return
    await message.answer(f" Вывод средств\n\n Баланс: {format_currency(user['balance'])}\n\n Вывод временно недоступен", parse_mode="HTML")

@router.callback_query(F.data == "add_payment_method")
async def add_payment_method_disabled(callback: CallbackQuery):
    await callback.answer(" Способы выплат временно недоступны", show_alert=True)

@router.callback_query(F.data == "view_payment_methods")
async def view_payment_methods_disabled(callback: CallbackQuery):
    await callback.answer(" Способы выплат временно недоступны", show_alert=True)
