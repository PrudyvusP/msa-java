import json
import logging
from datetime import datetime

from confluent_kafka import Consumer

from .db import BookingHistory

logger = logging.getLogger(__name__)


class BookingHistoryConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, session_factory):
        self._topic = topic
        self._session_factory = session_factory
        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": "booking-history-group",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self._consumer.subscribe([topic])

    def run(self):
        logger.info("BookingHistoryConsumer запущен, слушаю топик '%s'...", self._topic)
        try:
            while True:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error("Kafka error: %s", msg.error())
                    continue

                value = msg.value()
                if value is None:
                    continue

                self._handle_message(msg, value)
        except KeyboardInterrupt:
            logger.info("Остановка consumer...")
        finally:
            self._consumer.close()

    def _handle_message(self, msg, raw_value: bytes):
        try:
            event = json.loads(raw_value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error("Не удалось распарсить сообщение: %s", e)
            return

        event_type = event.get("type_")
        if event_type != "BOOKING_CREATED":
            logger.debug("Пропущено событие: %s", event_type)
            return

        payload = event.get("payload", {})
        happened_at_str = event.get("created_at")

        try:
            happened_at = datetime.fromisoformat(happened_at_str)
        except (TypeError, ValueError) as e:
            logger.error(
                "Не удалось распарсить happened_at '%s': %s", happened_at_str, e
            )
            return

        history = BookingHistory(
            id=payload["id"],
            user_id=payload["user_id"],
            hotel_id=payload["hotel_id"],
            promo_code=payload.get("promo_code"),
            discount_percent=payload.get("discount_percent", 0.0),
            price=payload["price"],
            happened_at=happened_at,
        )

        try:
            with self._session_factory() as session:
                session.merge(history)
                session.commit()

            self._consumer.commit(message=msg, asynchronous=True)

            logger.info(
                "Сохранено: id=%s user=%s hotel=%s price=%s happened_at=%s",
                history.id,
                history.user_id,
                history.hotel_id,
                history.price,
                history.happened_at,
            )
        except Exception:
            logger.error(
                "Ошибка сохранения, offset НЕ закоммичен. id=%s",
                history.id,
                exc_info=True,
            )
