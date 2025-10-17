import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date, datetime

# === Конфигурация ===
BOT_TOKEN = "8342746290:AAHZ-hr_0kjfF5RllgXdBML8B8x4FkvtZdQ"
TARGET_CHAT_ID = -1003025877026
MENTION_USER_ID = 7492286439
TOTAL_FLATS = 264

# === Настройка логов ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

# === /start ===
@dp.message(Command("start"))
async def start(message: Message):
    user_data[message.from_user.id] = {}
    today_str = datetime.today().strftime("%d.%m.%Y")
    user_data[message.from_user.id]["date"] = today_str
    await message.answer(f"📅 Сегодняшняя дата автоматически установлена: {today_str}\n\n🚪 Выбери подъезд:")
    await select_podyezd(message)

# === Подъезд ===
async def select_podyezd(message: Message):
    builder = InlineKeyboardBuilder()
    for p in ["1", "2", "Дворовая территория"]:
        builder.button(text=p, callback_data=f"podyezd:{p}")
    builder.adjust(1)
    await message.answer("🚪 Выбери подъезд:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("podyezd:"))
async def podyezd_selected(callback: CallbackQuery):
    _, podyezd = callback.data.split(":")
    user_data[callback.from_user.id]["podyezd"] = podyezd
    await callback.message.edit_text(f"✅ Подъезд: {podyezd}\nТеперь выбери квартиру.")
    await select_flat(callback.message, page=1)

# === Квартиры с пагинацией ===
FLATS_PER_PAGE = 20

async def select_flat(message: Message, page: int):
    builder = InlineKeyboardBuilder()
    start = (page - 1) * FLATS_PER_PAGE + 1
    end = min(start + FLATS_PER_PAGE - 1, TOTAL_FLATS)

    for i in range(start, end + 1):
        builder.button(text=str(i), callback_data=f"flat:{i}")

    if page > 1:
        builder.button(text="⬅️ Назад", callback_data=f"flat_page:{page-1}")
    if end < TOTAL_FLATS:
        builder.button(text="Вперёд ➡️", callback_data=f"flat_page:{page+1}")

    builder.adjust(5)
    await message.answer(f"🏠 Выбери квартиру ({start}-{end} из {TOTAL_FLATS}):", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("flat_page:"))
async def flats_page(callback: CallbackQuery):
    _, page = callback.data.split(":")
    await callback.message.delete()
    await select_flat(callback.message, int(page))

@dp.callback_query(F.data.startswith("flat:"))
async def flat_selected(callback: CallbackQuery):
    _, flat = callback.data.split(":")
    user_data[callback.from_user.id]["flat"] = flat
    await callback.message.edit_text(f"✅ Квартира: {flat}\nТеперь введи комментарий (сообщением):")

# === Комментарий и отправка ===
@dp.message(F.text)
async def comment_handler(message: Message):
    uid = message.from_user.id
    if uid not in user_data or "flat" not in user_data[uid]:
        return

    user_data[uid]["comment"] = message.text
    data = user_data[uid]
    formatted_date = data["date"]

    sender_name = message.from_user.full_name
    sender_id = message.from_user.id

    mention_text = f'<a href="tg://user?id={MENTION_USER_ID}">Получатель</a>'

    text = (
        f"📩 <b>Новая заявка!</b>\n\n"
        f"🗓 Дата: {formatted_date}\n"
        f"🚪 Подъезд: {data['podyezd']}\n"
        f"🏠 Квартира: {data['flat']}\n"
        f"💬 Комментарий: {data['comment']}\n\n"
        f"👤 Получатель: {mention_text}"
    )

    await bot.send_message(chat_id=TARGET_CHAT_ID, text=text, parse_mode="HTML")

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Подать новую заявку", callback_data="new_request")
    await message.answer("✅ Заявка отправлена в группу!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "new_request")
async def new_request(callback: CallbackQuery):
    await callback.message.edit_text("🚀 Начинаем новую заявку!")
    await start(callback.message)

# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())