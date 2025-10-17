import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

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
    await message.answer(
        f"📅 Дата: {today_str}\n\n🚪 Выбери подъезд:"
    )
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
    await callback.message.edit_text(
        f"✅ Подъезд: {podyezd}\nТеперь укажите номер вашей квартиры (от 1 до {TOTAL_FLATS}):"
    )

# === Ввод квартиры через сообщение ===
@dp.message(F.text)
async def flat_input(message: Message):
    uid = message.from_user.id
    if uid not in user_data:
        return

    # Проверяем, что пользователь выбрал подъезд, но ещё не ввёл квартиру
    if "podyezd" in user_data[uid] and "flat" not in user_data[uid]:
        if not message.text.isdigit():
            await message.answer(f"❌ Номер квартиры должен быть числом от 1 до {TOTAL_FLATS}. Попробуйте ещё раз.")
            return
        flat_number = int(message.text)
        if not (1 <= flat_number <= TOTAL_FLATS):
            await message.answer(f"❌ Квартира должна быть от 1 до {TOTAL_FLATS}. Попробуйте ещё раз.")
            return

        user_data[uid]["flat"] = str(flat_number)
        await message.answer("✅ Квартира сохранена.\nТеперь напишите: Какие работы необходимо провести")
        return

    # Комментарий
    if "flat" in user_data[uid] and "comment" not in user_data[uid]:
        user_data[uid]["comment"] = message.text
        data = user_data[uid]
        formatted_date = data["date"]

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

# === Начать новую заявку ===
@dp.callback_query(F.data == "new_request")
async def new_request(callback: CallbackQuery):
    await callback.message.edit_text("🚀 Начинаем новую заявку!")
    await start(callback.message)

# === Запуск ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())