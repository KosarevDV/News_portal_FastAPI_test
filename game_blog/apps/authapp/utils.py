import hashlib
import random
import string
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import MessageSchema, FastMail, ConnectionConfig
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from apps.authapp.models import User
from apps.authapp.models import Token

from apps.authapp.schemas import UserCreate
from core.config import mail_conf


def get_random_string(length=12):
    """ Генерирует случайную строку, использующуюся как соль """
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = get_random_string()

    enc = hashlib.pbkdf2_hmac('sha256', password.encode(),
						salt.encode(), 100_000)
    return enc.hex()


def validate_password(password: str, hashed_password: str):
    """ Проверяет, что хеш пароля совпадает с хешем из БД """
    salt, hashed = hashed_password.split('$')
    return hash_password(password, salt) == hashed


async def get_user_by_email(email: str, db: Session):
    """ Возвращает информацию о пользователе """
    user = db.query(User).filter(User.email == email).first()
    return user


async def get_user_by_token(token: str, db: Session):
    user = db.query(User).join(Token).filter(and_(Token.token == token, Token.expires > datetime.now())).first()
    return user


async def get_token_by_user(user_uid: str, db: Session):
    token = db.query(Token).filter(and_(Token.user_uid ==
		user_uid, Token.expires > datetime.now())).first()
    return token


async def create_user_token(user_uid: str, db: Session):
    '''Создаем объект токена пользователя на базе его идентификатора и выполняем запись в базу данных'''
    token = Token(
        expires=datetime.now() + timedelta(weeks=2),
        user_uid=user_uid,
    )
    db.add(token)
    db.commit()
    return token


async def do_hash_password(password):
    '''Получаем строку с солью пользователя и хешем пароля, т.к. в базу данных будем записывать именно строку'''
    salt = get_random_string()
    hashed_password = hash_password(password, salt)
    return f"{salt}${hashed_password}"

async def create_user(user: UserCreate, db: Session):
    """ Создает нового пользователя в БД """
    hashed_password = await do_hash_password(user.password)
    user_db = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(user_db)
    db.commit()
    db.refresh(user_db)

    user_uid = user_db.uid

    return {**user.dict(), 'uid': user_uid, 'is_active': True}


async def get_current_user(db: Session, token: str):
    '''возвращаем объект пользователя через его токен'''
    user = await get_user_by_token(token, db)
    return user


async def send_message(url, user: User):
    '''создание объекта сообщения для восстановления пароля пользователя'''
    html = f"""
    Для сброса пароля перейдите по адресу: '{url}'
    """
    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=[user.email],  # List of recipients, as many as you can pass
        body=html,
        subtype="html")

    #
    # mail_conf = ConnectionConfig(
    #     MAIL_USERNAME="testaccountruslan",
    #     MAIL_PASSWORD="ihildpyppazpehje",
    #     MAIL_FROM="testaccountruslan@yandex.ru",
    #     MAIL_PORT=465,
    #     MAIL_SERVER="smtp.yandex.ru",
    #     MAIL_FROM_NAME="Test Messages",
    #     MAIL_TLS=False,
    #     MAIL_SSL=True,
    #     USE_CREDENTIALS=True,
    #     VALIDATE_CERTS=True
    # )

    fm = FastMail(mail_conf)
    await fm.send_message(message)