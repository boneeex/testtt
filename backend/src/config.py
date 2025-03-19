from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent  # Assuming config.py is in backend/


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "pems" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "pems" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 2

    @property
    def private_key(self) -> bytes:
        with open(self.private_key_path, "rb") as key_file:
            return key_file.read()

    @property
    def public_key(self) -> bytes:
        with open(self.public_key_path, "rb") as key_file:
            return key_file.read()


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    # JWT Configuration
    auth_jwt: AuthJWT = Field(default_factory=lambda: AuthJWT())

    @property
    def DATABASE_URL_asyncpg(self):
        # postgresql+asyncpg://postgres:postgres@localhost:5432/sa
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()