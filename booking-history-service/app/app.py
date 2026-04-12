import logging
import os

from dotenv import load_dotenv

from .consumer import BookingHistoryConsumer
from .db import get_engine, get_session_factory, init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class Server:
    @staticmethod
    def run():
        kafka_server = os.getenv("KAFKA_SERVER", "kafka")
        kafka_port = os.getenv("KAFKA_PORT", "9092")
        kafka_topic = os.getenv("KAFKA_TOPIC", "booking-events")

        # Инициализация БД
        engine = get_engine()
        init_db(engine)
        session_factory = get_session_factory(engine)

        # Consumer
        consumer = BookingHistoryConsumer(
            bootstrap_servers=f"{kafka_server}:{kafka_port}",
            topic=kafka_topic,
            session_factory=session_factory,
        )
        consumer.run()


if __name__ == "__main__":
    Server.run()
