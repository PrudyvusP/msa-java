import os

from sqlalchemy import Column, DateTime, Float, String, create_engine, func, text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True)
    user_id = Column(String(255))
    hotel_id = Column(String(255))
    promo_code = Column(String(255))
    discount_percent = Column(Float)
    price = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def get_engine():
    user = os.getenv("POSTGRES_USER", "booking")
    password = os.getenv("POSTGRES_PASSWORD", "booking")
    host = os.getenv("POSTGRES_HOST", "booking-db")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "booking")

    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")


def init_db(engine):
    Base.metadata.create_all(engine)
    _load_fixtures(engine)


def _load_fixtures(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM bookings"))
        count = result.scalar()
        if count == 0:
            conn.execute(
                text("""
                INSERT INTO bookings (id, user_id, hotel_id, promo_code, discount_percent, price, created_at)
                VALUES
                    ('1000000000001', 'test-user-2', 'test-hotel-1', 'TESTCODE1', 10.0, 90.0, NOW()),
                    ('1000000000002', 'test-user-3', 'test-hotel-1', NULL, 0.0, 80.0, NOW())
            """)
            )
            conn.commit()


def get_session_factory(engine):
    return sessionmaker(bind=engine)
