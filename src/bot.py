from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import re
import os
from database import engine

from crud import *



TOKEN = os.getenv("TG_BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

reg_exp_duty_to_me = r'(@.{3,}) приторчал(а)? мне ([0-9]{,5}(.[0-9]{1,2})?)'
reg_exp_payday = r'(@.{3,}) вернул(а)? мне ([0-9]{,5}(.[0-9]{1,2})?)'
reg_exp_my_duty = r'Я задолжал(а)? (@.{3,}) ([0-9]{,5}(.[0-9]{1,2})?)'
reg_exp_wipe_duty = r'Прощаю долг (@.{3,})'


@dp.message_handler(commands=['start'])
async def send_welcome(msg: types.Message):
    await msg.answer(f'Я бот-счетовод. Приятно познакомиться, {msg.from_user.username}.\nДля просмотра команд введите /help')
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    if msg.from_user.username == 'brochachox':
        await msg.answer("Не забудь про должок Лёхе;)")



@dp.message_handler(commands=['help'])
async def send_docs(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    await msg.answer(
"""
*\<@Ник\> приторчал\(а\) мне \<Сума\>* \- _добавить долг вам_

*Я задолжал\(а\) \<@Ник\> \<Сума\>* \- _добавить ваш долг_

*Прощаю долг \<@Ник\>* \- _простить долг_

*\<@Ник\> вернул\(а\) мне \<Сума\>* \- _вычесть суму из долга_

*Кому я задолжал\(а\)\?* \- _посмотреть свои долги_

*Кто мне должен\?* \- _посмотреть должников_

*Сколько мне должны\?* \- _посмотреть сумарный долг тебе_

*Сколько я задолжал\(а\)\?* \- _посмотреть свой сумарный долг_
""", parse_mode="MarkdownV2")


@dp.message_handler(lambda msg: re.fullmatch(reg_exp_duty_to_me, msg.text))
async def add_duty_to_me(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    m = re.match(reg_exp_duty_to_me, msg.text)
    debtor = m.group(1)
    amount = m.group(3)
    duty = add_duty(str("@"+msg.from_user.username), str(debtor), float(amount))
    if not duty:
        await msg.answer("Вы в рассчете")
    else:
        user = get_user_info(duty.debtor)
        if user:
            await bot.send_message(user.chat_id, f'Вы заторчали {duty.lender} {duty.amount}')
        await msg.answer(f'У {debtor} должок {duty.amount}')


@dp.message_handler(lambda msg: re.fullmatch(reg_exp_my_duty, msg.text))
async def add_my_duty(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    m = re.match(reg_exp_my_duty, msg.text)
    lender = m.group(2)
    amount = m.group(3)
    duty = add_duty(str(lender), str("@"+msg.from_user.username), float(amount))
    if not duty:
        await msg.answer("Ты ничего не должен.")
    else:
        await msg.answer(f'Ты {"должна" if m.group(1) else "должен"} {duty.lender} {duty.amount}.')


@dp.message_handler(lambda msg: re.fullmatch(reg_exp_payday, msg.text))
async def get_payment(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    m = re.match(reg_exp_payday, msg.text)
    debtor = m.group(1)
    amount = m.group(3)
    await msg.answer(payday(str("@"+msg.from_user.username), debtor, float(amount)))


@dp.message_handler(lambda msg: re.fullmatch(r'Кому я задолжал(а)?[\?]', msg.text))
async def check_my_duties(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    m = re.match(r'Кому я задолжал((а)?)[\?]', msg.text)
    duties = get_my_duties(str("@"+msg.from_user.username))
    if not duties:
        await msg.answer("Пока долгов нету)")
    else:
        for duty in duties:
            await msg.answer(f'Ты {"должна" if m.group(1) else "должен"} {duty.lender} {duty.amount}.')


@dp.message_handler(lambda msg: re.fullmatch(r'Сколько я задолжал(а)?[\?]', msg.text))
async def count_my_duties(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    total_duty = count_my_total_duty(str("@"+msg.from_user.username))
    if total_duty:
        await msg.answer(f'Ты торчишь {total_duty}')
    else:
        await msg.answer("Никому ты не должен")


@dp.message_handler(lambda msg: msg.text == 'Кто мне должен?')
async def check_duties_to_me(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    duties = get_duties_for_me(str("@"+msg.from_user.username))
    if not duties:
        await msg.answer("Пока должников нету.")
    else:
        for duty in duties:
            await msg.answer(f'У {duty.debtor} должок {duty.amount}.')


@dp.message_handler(lambda msg: msg.text == 'Сколько мне должны?')
async def count_duties_to_me(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    total_duty = count_total_duty_to_me(str("@"+msg.from_user.username))
    if total_duty:
        await msg.answer(f'Тебе торчат {total_duty}')
    else:
        await msg.answer("Никто тебе не должен")


@dp.message_handler(lambda msg: re.fullmatch(reg_exp_wipe_duty, msg.text))
async def wipe_away_a_dept(msg: types.Message):
    sign_up_user(str("@"+msg.from_user.username), msg.from_user.id, msg.chat.id)
    m = re.match(reg_exp_wipe_duty, msg.text)
    debtor = m.group(1)
    if await wipe_away_the_dept(str("@"+msg.from_user.username), debtor, bot):
        await msg.answer("Долг прощен.")
    else:
        await msg.answer("Так он тебе и не должен нихрена.")


if __name__ == '__main__':
   if not os.path.exists('database.sqlite3'):
       print("Creating db...")
       tables.Base.metadata.create_all(engine)
       print("Db has been created.")
   executor.start_polling(dp)
