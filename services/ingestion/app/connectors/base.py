from abc import ABC, abstractmethod
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class BaseConnector(ABC):
    BATCH_SIZE = 500

    def __init__(self, db_url: str):
        if not db_url:
            raise ValueError(f"{self.__class__.__name__}: DB URL not configured")
        engine = create_engine(db_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=engine)

    @abstractmethod
    def fetch_members(self) -> Generator[list[dict], None, None]:
        pass

    def _fetch_batched(self, session, query: str, params: dict | None = None) -> Generator[list[dict], None, None]:
        offset = 0
        while True:
            rows = session.execute(
                text(query + f" LIMIT {self.BATCH_SIZE} OFFSET {offset}"),
                params or {},
            ).mappings().all()
            if not rows:
                break
            yield [dict(r) for r in rows]
            offset += self.BATCH_SIZE
