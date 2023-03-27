import time
from uuid import uuid4
import json
from authlib.jose import JsonWebSignature
from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType, UUIDType
import datetime
from apps.postapp.models import Post
from core.config import SECRET_KEY
from db.base_class import Base


class User(Base):

    uid = Column(UUIDType, default=uuid4, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    email = Column(EmailType)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    post = relationship("Post", back_populates="owner")
    token = Column(String(64), nullable=True)

    def get_reset_token(self, expires_sec=1800):
        '''метод для генерации токена, действует 1800сек'''
        # Создаем экземпляр токена с указанием алгоритма шифрования
        jws = JsonWebSignature(['HS256'])
        protected = {'alg': 'HS256'}
        # Определяем набор полей с полезной нагрузкой
        payload = json.dumps({'expires_sec': expires_sec,
                              'time_sending': time.time(),
                              'user_uid': str(self.uid)}).encode('utf-8')
        secret = SECRET_KEY
        # сериализация токена на базе указанного алгоритма, набора данных с полезной нагрузкой, секретного ключа
        return jws.serialize_compact(protected, payload, secret).decode('utf-8')

    @staticmethod
    def get_payload_from_reset_token(token):
        '''выполняем десериализацию на базе секретного ключа, возвращаем полезную нагрузку если токен не истек'''
        jws = JsonWebSignature(['HS256'])
        data = jws.deserialize_compact(token, SECRET_KEY)
        payload_json = json.loads(data['payload'])
        time_left = payload_json['time_sending'] + payload_json['expires_sec'] - time.time()
        print(time_left)
        if time_left < 0:
            return False
        else:
            return payload_json


class Token(Base):
    uid = Column(UUIDType, default=uuid4, primary_key=True)
    token = Column(UUIDType, unique=True, nullable=False, index=True, default=uuid4)
    expires = Column(DateTime())
    user_uid = Column(UUIDType, ForeignKey('user.uid'))
