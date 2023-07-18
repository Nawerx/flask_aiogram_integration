from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from werkzeug.security import check_password_hash
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.models import Note, User

from tg_bot.misc.states import LoginStates
from tg_bot.services.db import engine
async def send_welcome(message: types.Message):
    with Session(engine) as session:
        user = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()

    if user:
        await message.answer(f"вітаю {user.username}, щоб побачити список команд натисни меню або напиши команду /help")
    else:
        await message.answer("Вітаю незнайомець. Увійди у систему написавши команду /login")


async def help(message: types.Message):
    await message.answer("Ось список доступних команд\n"
                         "/start - перезапустити бота\n"
                         "/login - увійти в систему\n"
                         "/unlink - відв'язати телеграм від аккаунту\n"
                         "/help - подивитись список команд\n"
                         "/notes - передивитись свої замітки")


async def start_login_process(message: types.Message):
    await message.answer("Введіть свій логін")
    await LoginStates.login.set()


async def finishing_login_process(message: types.Message, state: FSMContext):
    if not (4 <= len(message.text) <= 64):
        await message.answer(f"логін має бути в межах від 4-ьох до 64-ьох символів")
        return

    await state.update_data(username=message.text)
    await message.answer(f"твій логін  {message.text}, тепер пиши пароль")
    await message.delete()
    await LoginStates.password.set()


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



async def unlink(message: types.Message):
    with Session(engine) as session:
        linked = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()
        linked.telegram_id = None
        session.commit()
        await message.answer("Ваш телеграм було успішно відв'язано")



async def show_notes(message: types.Message):
    with Session(engine) as session:
        user = session.execute(select(User).where(User.telegram_id == message.from_id)).scalar()
        notes = session.execute(select(Note).where(Note.author_id == user.id)).scalars()
        notes_markup = InlineKeyboardMarkup()
        for note in notes:
            notes_markup.add(
                InlineKeyboardButton(
                    note.title,
                    callback_data=f"note_{note.id}"
                )
            )
        await message.answer("ось ваші замітки:", reply_markup=notes_markup)



async def notes_button_handler(call: types.CallbackQuery):
    note_id = call.data.split("_")[1]
    button_func_markup = InlineKeyboardMarkup()
    but1 = InlineKeyboardButton("Видалити", callback_data=f"delete_{note_id}")
    but2 = InlineKeyboardButton("Змінити", callback_data=f"edit_{note_id}")
    button_func_markup.add(but1,but2)
    await call.message.answer("Що ви хочете зробити з цією заміткою?", reply_markup=button_func_markup)
    await call.answer()


async def delete_note(call: types.CallbackQuery):
    note_id = call.data.split("_")[1]
    with Session(engine) as session:
        note = session.execute(select(Note).where(Note.id == note_id)).scalar()
        title = note.title
        session.delete(note)
        session.commit()
    await call.message.answer(f"Замітку {title} було видалено")
    await call.answer()



async def start_edit_note(call: types.CallbackQuery, state: FSMContext):
    note_id = call.data.split("_")[1]
    await state.update_data(note_id=note_id)
    await call.message.answer("Введи нову назву: ")
    await LoginStates.edit_note.set()
    await call.answer()



async def finishing_edit_note(message: types.Message, state: FSMContext):
    note_id = (await state.get_data()).get("note_id")
    with Session(engine) as session:
        note = session.execute(select(Note).where(Note.id == note_id)).scalar()
        note.content = message.text
        session.commit()
    await message.answer(f"Назву замітки було змінено на {message.text}")
    await state.finish()



async def not_showed_notes(message: types.Message):
    if message.text == "/notes":
        await message.answer("Щоб подивитись нотатки треба увійти в систему за допомогую команди /login")
    elif message.text == "/unlink":
        await message.answer("Ваш телеграм не прив'язаний до жодного аккаунту, ви можете це зробити за допомогою команди /login")



def register_user(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start'], state="*")
    dp.register_message_handler(help, commands=['help'], state="*")
    dp.register_message_handler(start_login_process, commands=['login'], state="*")
    dp.register_message_handler(finishing_login_process, state=LoginStates.login, content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(check_password, state=LoginStates.password, content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(unlink, commands=["unlink"], state="*", is_linked=True)
    dp.register_message_handler(show_notes, commands=["notes"], state="*", is_linked=True)
    dp.register_callback_query_handler(notes_button_handler, lambda c: c.data.startswith("note_"))
    dp.register_callback_query_handler(delete_note, lambda c: c.data.startswith("delete_"))
    dp.register_callback_query_handler(start_edit_note, lambda c: c.data.startswith("edit_"))
    dp.register_message_handler(finishing_edit_note, state=LoginStates.edit_note, content_types=types.ContentTypes.TEXT)
    dp.register_message_handler(not_showed_notes, commands=["notes", "unlink"], state="*", is_linked=False)

