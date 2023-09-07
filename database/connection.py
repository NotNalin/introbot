from urllib.parse import quote_plus

from decouple import config
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool


class DBConnection:
    def __init__(self, pool_size=5, max_overflow=10):
        db_host = config("DB_HOST")
        db_user = config("DB_USER")
        db_pass = quote_plus(config("DB_PASS"))
        db_name = config("DB_NAME")
        db_port = config("DB_PORT", cast=int)
        self.db_engine = create_engine(
            url=f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}',
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True
        )

    def execute(self, query, params=None):
        with Session(self.db_engine) as session:
            session.execute(text(query), params)
            session.commit()

    def fetch_all(self, query, params=None):
        with Session(self.db_engine) as session:
            result = session.execute(text(query), params)
            session.commit()
            return result.fetchall()

    def fetch_one(self, query, params=None):
        with Session(self.db_engine) as session:
            result = session.execute(text(query), params)
            session.commit()
            return result.fetchone()

    def fetch_single_data(self, query, params=None):
        result = self.fetch_one(query, params)
        if result and result[0]:
            return result[0]
