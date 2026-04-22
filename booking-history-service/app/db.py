import os

from sqlalchemy import Column, DateTime, Float, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class BookingHistory(Base):
    __tablename__ = "booking_history"

    id = Column(String, primary_key=True)
    user_id = Column(String(255))
    hotel_id = Column(String(255))
    promo_code = Column(String(255))
    discount_percent = Column(Float)
    price = Column(Float, nullable=False)
    happened_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def get_engine():
    user = os.getenv("POSTGRES_USER", "booking_history")
    password = os.getenv("POSTGRES_PASSWORD", "booking_history")
    host = os.getenv("POSTGRES_HOST", "history-db")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "booking_history")

    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")


def init_db(engine):
    Base.metadata.create_all(engine)


def get_session_factory(engine):
    return sessionmaker(bind=engine)
