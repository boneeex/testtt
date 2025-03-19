import jwt
import bcrypt
import datetime
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import random
import string

from src.database import async_engine, Base
from .config import settings
from .db_action.queries import Users

#database creation
async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def generate_unique_code():
    # Define possible characters: uppercase letters and digits.
    characters = string.ascii_uppercase + string.digits
    # Generate a random code of 6 characters.
    code = ''.join(random.choices(characters, k=6))
    return code


class PasswordActions:
    @staticmethod
    def hash(password: str) -> str:
        """Генерирует хеш пароля в формате строки"""
        salt = bcrypt.gensalt()
        pwd_bytes: bytes = password.encode()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')  # Конвертируем байты в строку

    @staticmethod
    def validate(password: str, hashed_password: str) -> bool:
        """Проверяет соответствие пароля хешу"""
        return bcrypt.checkpw(
            password=password.encode(),
            hashed_password=hashed_password.encode('utf-8')  # Конвертируем обратно в байты
        )


class JWTActions:
    @staticmethod
    def encode(payload: dict,
               private_key: str = settings.auth_jwt.private_key_path.read_text(), 
               algorithm: str = settings.auth_jwt.algorithm,
               expire_timedelta: datetime.timedelta | None = None,
               expire_minutes: int = settings.auth_jwt.access_token_expire_minutes
               ):
        to_encode = payload.copy()
        now = datetime.datetime.utcnow()
        if expire_timedelta:
            expire = now + expire_timedelta
        else:
            expire = now + datetime.timedelta(minutes=expire_minutes)
        to_encode.update(exp=expire, iat=now)
        encoded = jwt.encode(to_encode, private_key, algorithm=algorithm)
        return encoded

    @staticmethod
    def decode(token: str | bytes, 
               public_key: str = settings.auth_jwt.public_key_path.read_text(), 
               algorithm: str = settings.auth_jwt.algorithm
               ):
        decoded = jwt.decode(token, public_key, algorithms=[algorithm])
        return decoded
    

class AuthActions:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/teachers/login")

    @staticmethod
    def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> dict:
        try:
            payload = JWTActions.decode(
                token=token,
            )
        except InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"invalid token error: {e}",
            )
        return payload
    
    @staticmethod
    async def validate_user(token: str) -> bool:
        payload = AuthActions.get_current_token_payload(token=token)
        user_email = payload['sub']
        user_exists = await Users.check_teacher_uniqueness_and_return_password(user_email=user_email)
        if bool(user_exists):
            return True
        raise HTTPException(status_code=403, detail="Пользователь не авторизован")