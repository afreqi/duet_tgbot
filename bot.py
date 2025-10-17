import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

# === Конфигурация ===
BOT_TOKEN = "8342746290:AAHZ-hr_0kjfF5RllgXdBML8B8x4FkvtZdQ"
TARGET_CHAT_ID = --1003025877026  # <-- ID группы
MENTION_USER_IDS = [7492286439, 7604321833]  # <-- список получателей
TOTAL_FLATS = 264
TOTAL_FLOORS = 24
FLATS_PER_PAGE = 20  # кол-во квартир на одной странице

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
    await message.answer(f"🗓 Дата: {today_str}\n\n🚪 Выбери подъезд:")
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

    if podyezd in ["1", "2"]:
        await callback.message.edit_text(f"✅ Подъезд: {podyezd}\nТеперь выбери этаж:")
        await select_floor(callback.message)
    else:
        await callback.message.edit_text(f"✅ Подъезд: {podyezd}")
        await select_flat(callback.message, page=1)

# === Этаж ===
async def select_floor(message: Message):
    builder = InlineKeyboardBuilder()
    for i in range(1, TOTAL_FLOORS + 1):
        builder.button(text=str(i), callback_data=f"floor:{i}")
    builder.adjust(4)
    await message.answer("🏢 Выбери этаж:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("floor:"))
async def floor_selected(callback: CallbackQuery):
    _, floor = callback.data.split(":")
    user_data[callback.from_user.id]["floor"] = floor
    await callback.message.edit_text(f"✅ Этаж: {floor}")
    await select_flat(callback.message, page=1)

# === Квартиры (с пагинацией) ===
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
    await callback.message.edit_text(f"✅ Квартира: {flat}\n🛠 Какие работы необходимо провести?")

# === Комментарий и отправка ===
@dp.message(F.text)
async def comment_handler(message: Message):
    uid = message.from_user.id
    if uid not in user_data or "flat" not in user_data[uid]:
        return

    user_data[uid]["comment"] = message.text
    data = user_data[uid]

    formatted_date = data["date"]
    mentions = ", ".join([f'<a href="tg://user?id={uid}">Получатель</a>' for uid in MENTION_USER_IDS])

    text = (
        f"📩 <b>Новая заявка!</b>\n\n"
        f"🗓 Дата: {formatted_date}\n"
        f"🚪 Подъезд: {data['podyezd']}\n"
    )

    if "floor" in data:
        text += f"🏢 Этаж: {data['floor']}\n"

    text += (
        f"🏠 Квартира: {data['flat']}\n"
        f"💬 Комментарий: {data['comment']}\n\n"
        f"👤 Получатели: {mentions}"
    )

    await bot.send_message(chat_id=TARGET_CHAT_ID, text=text, parse_mode="HTML")

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Подать новую заявку", callback_data="new_request")
    await message.answer("✅ Заявка отправлена в группу!", reply_markup=builder.as_markup())

# === Новая заявка ===
@dp.callback_query(F.data == "new_request")
async def new_request(callback: CallbackQuery):
    await callback.message.edit_text("🚀 Начинаем новую заявку!")
    await start(callback.message)

# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
