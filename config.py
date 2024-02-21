from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALGORITHM_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES: int
    CRYPTOCOMPARE_API_KEY: str
    MIDDLEWARE_KEY: str
    MODE: Literal['DEV', 'TEST', 'PROD']
    CRYPTOGRAPHY_KEY: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str


    @property
    def DATABASE_URL(self):
        return (f'postgresql+asyncpg://{self.DB_USER}:'
                f'{self.DB_PASS}@{self.DB_HOST}:'
                f'{self.DB_PORT}/{self.DB_NAME}')

    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_USER: str
    TEST_DB_PASS: str
    TEST_DB_NAME: str

    @property
    def DATABASE_TEST_URL(self):
        return (f'postgresql+asyncpg://{self.TEST_DB_USER}:'
                f'{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:'
                f'{self.TEST_DB_PORT}/{self.TEST_DB_NAME}')
    class Config:
        env_file = '.env'

settings = Settings()