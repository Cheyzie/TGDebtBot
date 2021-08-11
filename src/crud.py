from sqlalchemy.orm import Session, session
from database import get_session
import tables
from functools import reduce
from aiogram import Bot

def sign_up_user(username: str, user_id:int, chat_id: int):
    session = next(get_session())
    try:
        user = session.query(tables.UserInfo).filter(tables.UserInfo.user_id == user_id).first()
    except:
        ...
    if not user:
        user = tables.UserInfo(username=username, user_id=user_id, chat_id=chat_id)
        session.add(user)
    else:
        if user.chat_id != chat_id:
            user.chat_id = chat_id
        if user.username != username:
            update_username(user.username, username)
            user.username = username
    session.commit()

def update_username(old_username: str, new_username):
    session = next(get_session())
    duties = session.query(tables.Duty).filter(tables.Duty.debtor==old_username).all()
    for duty in duties:
        duty.username = new_username
    duties = session.query(tables.Duty).filter(tables.Duty.lender==old_username).all()
    for duty in duties:
        duty.username = new_username


def get_user_info(username: str):
    session = next(get_session())
    user = session.query(tables.UserInfo).filter(tables.UserInfo.username == username).first()
    if not user:
        return None
    return user

def get_duty(lender: str, debtor: str, session: Session) -> tables.Duty:
    duty = (session
        .query(tables.Duty)
        .filter(tables.Duty.lender==lender)
        .filter(tables.Duty.debtor==debtor)
        .first())
    return duty
def add_duty(lender: str, debtor: str, amount: float):
    session = next(get_session())
    duty = get_duty(lender, debtor, session)
    anti_duty = get_duty(debtor, lender, session)
    if anti_duty:
        if anti_duty.amount >= amount:
            anti_duty.amount -= amount
            if anti_duty.amount == 0:
                session.delete(anti_duty)
            session.commit()
            amount = 0
        else: 
            amount -= anti_duty.amount
            anti_duty.amount = 0
            session.commit()

    if not duty and amount != 0:
        duty = tables.Duty(lender=lender, debtor=debtor, amount=amount)
        session.add(duty)
        
    elif duty and amount != 0:
        duty.amount += amount
    if duty:
        session.commit()
        session.refresh(duty)
        return duty

def get_my_duties(debtor: str):
    session = next(get_session())
    duties = session.query(tables.Duty).filter(tables.Duty.debtor==debtor).all()
    return duties

def get_duties_for_me(lender: str):
    session = next(get_session())
    duties = session.query(tables.Duty).filter(tables.Duty.lender==lender).all()
    return duties

async def wipe_away_the_dept(lender: str, debtor: str, bot: Bot):
    session = next(get_session())
    duty = get_duty(lender, debtor,session)
    if not duty:
        return False
    user = get_user_info(duty.debtor)
    if user:
        await bot.send_message(user.chat_id, f'{duty.lender} простил вам {duty.amount}')        
    session.delete(duty)
    session.commit()
    return True

def count_my_total_duty(debtor: str):
    session = next(get_session())
    duties = (session
        .query(tables.Duty.amount)
        .filter(tables.Duty.debtor==debtor)
        .all())
    if not duties:
        return 0
    elif len(duties) == 1:
        return duties[0][0]
    return reduce(lambda a, b: a[0] + b[0], duties)

def count_total_duty_to_me(lender: str):
    session = next(get_session())
    duties = (session
        .query(tables.Duty.amount)
        .filter(tables.Duty.lender==lender)
        .all())
    if not duties:
        return 0
    elif len(duties) == 1:
        return duties[0][0]
    return reduce(lambda a, b: a[0] + b[0], duties)

def payday(lender: str, debtor: str, amount: float):
    session = next(get_session())
    duty = get_duty(lender, debtor,session)
    if not duty:
        duty = add_duty(lender=debtor, debtor=lender, amount=amount)
        return f'Верни ему деньги, {debtor} тебе не должен.\nЯ записал твой должок, негодяй!'
    if duty.amount < amount:
        amount -= duty.amount
        session.delete(duty)
        session.commit()
        duty = add_duty(lender=debtor, debtor=lender, amount=amount)
        return f'Ну теперь ты торчишь {duty.lender} {duty.amount}'
    elif duty.amount == amount:
        session.delete(duty)
        session.commit()
        return "Вы в рассчете."
    else:
        duty.amount -= amount
        session.commit()
        session.refresh(duty)
        return f'{duty.debtor} торчит тебе ещё {duty.amount}'