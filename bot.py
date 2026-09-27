import asyncio
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Booking(StatesGroup):
    name = State()
    phone = State()
    date = State()
    time = State()
    guests = State()


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Забронировать столик", callback_data="book")],
            [InlineKeyboardButton(text="Меню", callback_data="menu")],
        ]
    )


MENU_TEXT = (
    "<b>Меню «Манас»</b>\n\n"
    "☕ Флэт уайт — 180 сом\n"
    "☕ Капучино — 160 сом\n"
    "☕ Раф с облепихой — 220 сом\n"
    "☕ Американо — 130 сом\n"
    "🍰 Чизкейк «Бишкек» — 210 сом\n"
    "🥯 Боорсоки медовые — 150 сом\n"
    "🥐 Круассан миндальный — 190 сом\n"
    "🍵 Матча-латте — 200 сом"
)


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Это кофейня «Манас». Выберите действие:",
        reply_markup=start_keyboard(),
    )


@dp.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery):
    await callback.message.answer(MENU_TEXT, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Как вас зовут?", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Booking.name)
    await callback.answer()


@dp.message(Booking.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Ваш номер телефона?")
    await state.set_state(Booking.phone)


@dp.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("На какую дату? (например, 30.09)")
    await state.set_state(Booking.date)


@dp.message(Booking.date)
async def get_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("На какое время? (например, 19:00)")
    await state.set_state(Booking.time)


@dp.message(Booking.time)
async def get_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("Сколько человек будет?")
    await state.set_state(Booking.guests)


@dp.message(Booking.guests)
async def get_guests(message: Message, state: FSMContext):
    data = await state.update_data(guests=message.text)

    summary = (
        "<b>Заявка на бронь принята ✅</b>\n\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Гостей: {data['guests']}\n\n"
        "Мы свяжемся с вами для подтверждения."
    )
    await message.answer(summary, parse_mode="HTML", reply_markup=start_keyboard())

    if ADMIN_CHAT_ID:
        admin_text = (
            f"🔔 Новая бронь ({datetime.now().strftime('%d.%m %H:%M')})\n\n"
            f"От: @{message.from_user.username or message.from_user.first_name}\n"
            f"Имя: {data['name']}\n"
            f"Телефон: {data['phone']}\n"
            f"Дата: {data['date']}, время: {data['time']}\n"
            f"Гостей: {data['guests']}"
        )
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
