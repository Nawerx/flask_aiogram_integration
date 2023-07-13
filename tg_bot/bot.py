import logging
import hashlib
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import load_config
from models.models import User, Note
from sqlalchemy import select, URL, create_engine
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

cfg = load_config()

bot_token = cfg.tg.token




url = URL.create(
    drivername='postgresql+psycopg2',
    username=cfg.db.user,
    password=cfg.db.password,
    host=cfg.db.host,
    port=cfg.db.port,
    database=cfg.db.database
).render_as_string(hide_password=False)

engine = create_engine(url, echo=True)

class LoginStates(StatesGroup):
    login = State()
    password = State()
    loggedIn = State()
    edit_note = State()

API_TOKEN = bot_token


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot, storage=MemoryStorage())



@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    with Session(engine) as session:
        user = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()

    if user:
        await message.answer(f"вітаю {user.username}, щоб побачити список команд натисни меню або напиши команду /help")
    else:
        await message.answer("Вітаю незнайомець. Увійди у систему написавши команду /login")

@dp.message_handler(commands=['help'], state="*")
async def help(message: types.Message):
    await message.answer("Ось список доступних команд\n"
                         "/start - перезапустити бота\n"
                         "/login - увійти в систему\n"
                         "/unlink - відв'язати телеграм від аккаунту\n"
                         "/help - подивитись список команд")

@dp.message_handler(commands=['login'], state="*")
async def start_login_process(message: types.Message):
    await message.answer("Введіть свій логін")
    await LoginStates.login.set()

@dp.message_handler(state = LoginStates.login, content_types=types.ContentTypes.TEXT)
async def finishing_login_process(message: types.Message, state: FSMContext):
    if not (4 <= len(message.text) <= 64):
        await message.answer(f"логін має бути в межах від 4-ьох до 64-ьох символів")
        return

    await state.update_data(username=message.text)
    await message.answer(f"твій логін  {message.text}, тепер пиши пароль")
    await message.delete()
    await LoginStates.password.set()

@dp.message_handler(state=LoginStates.password, content_types=types.ContentTypes.TEXT)
async def check_password(message: types.Message, state: FSMContext):
    login = (await state.get_data()).get("username")
    password = message.text
    await message.delete()
    with Session(engine) as session:
        user = session.execute(select(User).where(User.username == login)).scalar()
        link = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()

        if not user or not check_password_hash(user.password, password):
            await message.answer("Неправильний логін або пароль")
            await start_login_process(message, state)
            return

        elif link and link != user: # if want to link another account
            await message.answer("цей телеграм вже прив'язаний до іншого аккаунту, переприв'яжіть цей аккаунт за допомогую команди /unlink")

        elif link == user: # link = account
            await message.answer("ваш телеграм вже прив'язано до цього аккаунту")
            await message.answer(f"Вітаю {login}")

        elif user.telegram_id != None:
            await message.answer("цей аккаунт вже прив'язанний до іншого телеграму, переприв'яжіть цей аккаунт за допомогую команди /unlink")

        else:
            user.telegram_id = message.from_id
            session.commit()
            await message.answer(f"Вітаю, {login}, ваш телеграм прив'язано до вашого аккаунту")

    await state.finish()


@dp.message_handler(commands=["unlink"], state="*")
async def unlink(message: types.Message):
    with Session(engine) as session:
        linked = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()
        if not linked:
            await message.answer("Ваш телеграм не прив'язаний до жодного аккаунту. Прив'яєіть телеграм за домогую команди /login")
            return
        linked.telegram_id = None
        session.commit()
        await message.answer("Ваш телеграм було успішно відв'язано")


@dp.message_handler(commands=["notes"], state="*") # 3кол бек дата хендлера -- note_id;delete_id;edit_id
async def show_notes(message: types.Message):
    with Session(engine) as session:
        user = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()
        notes = session.execute(select(Note).where(Note.author_id == user.id)).scalars()
        notes_markup = InlineKeyboardMarkup()
        for note in notes:
            notes_markup.add(
                InlineKeyboardButton(
                    note.content,
                    callback_data=f"note_{note.id}"
                )
            )
        await message.answer("ось ваші замітки:", reply_markup=notes_markup)



@dp.callback_query_handler(lambda c: c.data.startswith("note_"))
async def notes_button_handler(call: types.CallbackQuery):
    note_id = call.data.split("_")[1]
    button_func_markup = InlineKeyboardMarkup()
    but1 = InlineKeyboardButton("Видалити", callback_data=f"delete_{note_id}")
    but2 = InlineKeyboardButton("Змінити", callback_data=f"edit_{note_id}")
    button_func_markup.add(but1,but2)
    await bot.send_message(call.from_user.id, "Що ви хочете зробити з цією заміткою?", reply_markup=button_func_markup)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("delete_"))
async def delete_note(call: types.CallbackQuery):
    note_id = call.data.split("_")[1]
    with Session(engine) as session:
        note = session.execute(select(Note).where(Note.id == note_id)).scalar()
        content = note.content
        session.delete(note)
        session.commit()
    await bot.send_message(call.from_user.id, f"Замітку {content} було видалено")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("edit_"))
async def start_edit_note(call: types.CallbackQuery, state: FSMContext):
    note_id = call.data.split("_")[1]
    await state.update_data(note_id=note_id)
    await bot.send_message(call.from_user.id, "Введи нову назву: ")
    await LoginStates.edit_note.set()
    await call.answer()


@dp.message_handler(state=LoginStates.edit_note, content_types=types.ContentTypes.TEXT)
async def finishing_edit_note(message: types.Message, state: FSMContext):
    note_id = (await state.get_data()).get("note_id")
    with Session(engine) as session:
        note = session.execute(select(Note).where(Note.id == note_id)).scalar()
        note.content = message.text
        session.commit()
    await message.answer(f"Назву замітки було змінено на {message.text}")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)





