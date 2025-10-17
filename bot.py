import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

# === Конфигурация ===
BOT_TOKEN = "8342746290:AAHZ-hr_0kjfF5RllgXdBML8B8x4FkvtZdQ"
TARGET_CHAT_ID = -1003025877026
MENTION_USER_IDS = [7492286439, 7604321833]
TOTAL_FLATS = 264
TOTAL_FLOORS = 24
FLATS_PER_PAGE = 20

# === Логи ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

# === /start ===
@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    today_str = datetime.today().strftime("%d.%m.%Y")
    user_data[uid] = {"date": today_str}

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Запустить бота")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        f"🗓 Дата: {today_str}\n\nНажми кнопку, чтобы начать работу с ботом:",
        reply_markup=keyboard
    )

# 🔹 Кнопка запуска
@dp.message(F.text == "🚀 Запустить бота")
async def launch_bot(message: Message):
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
    uid = callback.from_user.id
    _, podyezd = callback.data.split(":")

    if uid not in user_data:
        user_data[uid] = {"date": datetime.today().strftime("%d.%m.%Y")}

    user_data[uid]["podyezd"] = podyezd

    if podyezd in ["1", "2"]:
        await callback.message.answer(f"✅ Подъезд: {podyezd}\nТеперь выбери этаж:")
        await select_floor(callback.message)
    else:
        # Дворовая территория → пропуск этажей и квартир
        await callback.message.answer(f"✅ Подъезд: {podyezd}\n✏️ Какие работы необходимо провести? (напиши сообщением)")

# === Этаж ===
async def select_floor(message: Message):
    uid = message.from_user.id
    if uid not in user_data:
        user_data[uid] = {"date": datetime.today().strftime("%d.%m.%Y")}

    builder = InlineKeyboardBuilder()
    for i in range(1, TOTAL_FLOORS + 1):
        builder.button(text=str(i), callback_data=f"floor:{i}")
    builder.adjust(4)
    await message.answer("🏢 Выбери этаж:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("floor:"))
async def floor_selected(callback: CallbackQuery):
    uid = callback.from_user.id
    _, floor = callback.data.split(":")
    if uid not in user_data:
        user_data[uid] = {"date": datetime.today().strftime("%d.%m.%Y")}
    user_data[uid]["floor"] = floor
    await callback.message.answer(f"✅ Этаж: {floor}\nТеперь выбери квартиру.")
    await select_flat(callback.message, page=1)

# === Квартиры с учетом подъезда ===
async def select_flat(message: Message, page: int):
    uid = message.from_user.id
    if uid not in user_data:
        user_data[uid] = {"date": datetime.today().strftime("%d.%m.%Y")}

    podyezd = user_data[uid].get("podyezd")
    if not podyezd or podyezd == "Дворовая территория":
        return  # не показываем клавиатуру для дворовой территории

    # Диапазон квартир по подъезду
    start_flat, end_flat = (1, 132) if podyezd == "1" else (133, 264)

    builder = InlineKeyboardBuilder()
    start = start_flat + (page - 1) * FLATS_PER_PAGE
    end = min(start + FLATS_PER_PAGE - 1, end_flat)

    for i in range(start, end + 1):
        builder.button(text=str(i), callback_data=f"flat:{i}")

    if page > 1:
        builder.button(text="⬅️ Назад", callback_data=f"flat_page:{page-1}")
    if end < end_flat:
        builder.button(text="Вперёд ➡️", callback_data=f"flat_page:{page+1}")

    builder.adjust(5)
    await message.answer(f"🏠 Выбери квартиру ({start}-{end} из {end_flat}):", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("flat_page:"))
async def flats_page(callback: CallbackQuery):
    uid = callback.from_user.id
    _, page = callback.data.split(":")
    await callback.message.delete()
    await select_flat(callback.message, int(page))

@dp.callback_query(F.data.startswith("flat:"))
async def flat_selected(callback: CallbackQuery):
    uid = callback.from_user.id
    _, flat = callback.data.split(":")
    user_data[uid]["flat"] = flat
    await callback.message.answer(f"✅ Квартира: {flat}\n\n✏️ Какие работы необходимо провести? (напиши сообщением)")

# === Комментарий и отправка ===
@dp.message(F.text)
async def comment_handler(message: Message):
    uid = message.from_user.id
    if uid not in user_data:
        return
    data = user_data[uid]
    if "flat" not in data and data.get("podyezd") in ["1", "2"]:
        return  # квартира обязателен для подъездов 1 и 2

    data["comment"] = message.text
    formatted_date = data["date"]

    mentions = " ".join(
        [f'<a href="tg://user?id={uid}">Получатель</a>' for uid in MENTION_USER_IDS]
    )

    text = (
        f"📩 <b>Новая заявка!</b>\n\n"
        f"🗓 Дата: {formatted_date}\n"
        f"🚪 Подъезд: {data.get('podyezd', '-')}\n"
        + (f"🏢 Этаж: {data.get('floor', '-')}\n" if "floor" in data else "")
        + (f"🏠 Квартира: {data.get('flat', '-')}\n" if "flat" in data else "")
        + f"💬 Комментарий: {data['comment']}\n\n"
        f"👤 Получатели: {mentions}"
    )

    await bot.send_message(chat_id=TARGET_CHAT_ID, text=text, parse_mode="HTML")

    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Подать новую заявку", callback_data="new_request")
    await message.answer("✅ Заявка отправлена в группу!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "new_request")
async def new_request(callback: CallbackQuery):
    await callback.message.answer("🚀 Начинаем новую заявку!")
    await start(callback.message)

# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



