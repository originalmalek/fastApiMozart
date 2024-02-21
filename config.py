from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALGORITHM_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES: int
    CRYPTOCOMPARE_API_KEY: str
    MIDDLEWARE_KEY: str
    MODE: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    CRYPTOGRAPHY_KEY: str

    @property
    def DATABASE_URL(self):
        return (f'postgresql+asyncpg://{self.DB_USER}:'
                f'{self.DB_PASS}@{self.DB_HOST}:'
                f'{self.DB_PORT}/{self.DB_NAME}')
    class Config:
        env_file = '.env'

settings = Settings()