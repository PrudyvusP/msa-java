import json
import logging
import sys
from datetime import datetime, timezone

from confluent_kafka import KafkaError, Message, Producer

from .interfaces.booking_producer import IBookingEventProducer

logger = logging.getLogger(__name__)


class BookingEventProducer(IBookingEventProducer):
    def __init__(self, topic: str, producer: Producer) -> None:
        self._topic = topic
        self._producer = producer

    def publish(self, booking: dict) -> None:
        event = {
            "type_": "BOOKING_CREATED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": booking,
        }
        self._producer.produce(
            topic=self._topic,
            value=json.dumps(event).encode("utf-8"),
            callback=self._delivery_callback,
        )
        self._producer.poll(1.0)
        remaining = self._producer.flush(timeout=5.0)
        if remaining > 0:
            logger.error("Не доставлено %d сообщений", remaining)
        else:
            logger.info("Событие BOOKING_CREATED отправлено в Kafka")

    @staticmethod
    def _delivery_callback(err: KafkaError | None, msg: Message):
        if err:
            sys.stderr.write("%% Сообщение не доставлено из-за ошибки: %s\n" % err)
        else:
            sys.stderr.write(
                "%% Сообщение доставлено: %s [%d] @ %d\n"
                % (msg.topic(), msg.partition(), msg.offset())
            )
