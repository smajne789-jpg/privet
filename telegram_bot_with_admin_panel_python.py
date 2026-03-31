import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# ENV
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

DATA_FILE = "config.json"

# ===== CONFIG =====
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({
            "text": "Добро пожаловать 👋",
            "image": None,
            "buttons": []
        }, f)


def load_config():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ===== FSM =====
class AdminStates(StatesGroup):
    waiting_text = State()
    waiting_image = State()
    waiting_button = State()


# ===== KEYBOARD =====
def build_keyboard(buttons):
    kb = InlineKeyboardMarkup(row_width=1)
    for btn in buttons:
        kb.add(InlineKeyboardButton(text=btn["text"], url=btn["url"]))
    return kb


# ===== START =====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    config = load_config()
    kb = build_keyboard(config["buttons"])

    if config["image"]:
        await bot.send_photo(
            message.chat.id,
            config["image"],
            caption=config["text"],
            reply_markup=kb
        )
    else:
        await message.answer(config["text"], reply_markup=kb)


# ===== ADMIN PANEL =====
@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ Нет доступа")

    await message.answer(
        "⚙️ Админ панель:\n\n"
        "/set_text — изменить текст\n"
        "/set_image — изменить картинку\n"
        "/add_button — добавить кнопку\n"
        "/clear_buttons — удалить кнопки"
    )


# ===== TEXT =====
@dp.message_handler(commands=["set_text"])
async def set_text(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await AdminStates.waiting_text.set()
    await message.answer("✏️ Отправь новый текст")


@dp.message_handler(state=AdminStates.waiting_text)
async def save_text(message: types.Message, state: FSMContext):
    config = load_config()
    config["text"] = message.text
    save_config(config)

    await message.answer("✅ Текст обновлен")
    await state.finish()


# ===== IMAGE =====
@dp.message_handler(commands=["set_image"])
async def set_image(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await AdminStates.waiting_image.set()
    await message.answer("🖼 Отправь изображение")


@dp.message_handler(content_types=["photo"], state=AdminStates.waiting_image)
async def save_image(message: types.Message, state: FSMContext):
    config = load_config()
    config["image"] = message.photo[-1].file_id
    save_config(config)

    await message.answer("✅ Картинка обновлена")
    await state.finish()


# ===== BUTTON =====
@dp.message_handler(commands=["add_button"])
async def add_button(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await AdminStates.waiting_button.set()
    await message.answer("🔗 Формат: Текст | Ссылка")


@dp.message_handler(state=AdminStates.waiting_button)
async def save_button(message: types.Message, state: FSMContext):
    try:
        text, url = message.text.split("|")

        config = load_config()
        config["buttons"].append({
            "text": text.strip(),
            "url": url.strip()
        })
        save_config(config)

        await message.answer("✅ Кнопка добавлена")
    except:
        await message.answer("❌ Ошибка. Формат: Текст | Ссылка")

    await state.finish()


# ===== CLEAR =====
@dp.message_handler(commands=["clear_buttons"])
async def clear_buttons(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    config = load_config()
    config["buttons"] = []
    save_config(config)

    await message.answer("🗑 Кнопки удалены")


# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
