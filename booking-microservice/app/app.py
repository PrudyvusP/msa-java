import logging
import os
from concurrent import futures

import grpc
from confluent_kafka import Producer
from dotenv import load_dotenv

from .db import get_engine, get_session_factory, init_db
from .generated import booking_pb2_grpc
from .producer import BookingEventProducer
from .service import BookingServiceServicer

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class Server:
    @staticmethod
    def run():
        grpc_port = os.getenv("GRPC_PORT", "9090")
        kafka_server = os.getenv("KAFKA_SERVER", "kafka")
        kafka_port = os.getenv("KAFKA_PORT", "9092")
        kafka_booking_topic = os.getenv("KAFKA_BOOKING_TOPIC", "booking-events")

        engine = get_engine()
        init_db(engine)
        session_factory = get_session_factory(engine)

        booking_producer = BookingEventProducer(
            topic=kafka_booking_topic,
            producer=Producer({"bootstrap.servers": f"{kafka_server}:{kafka_port}"}),
        )

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_servicer = BookingServiceServicer(booking_producer, session_factory)
        booking_pb2_grpc.add_BookingServiceServicer_to_server(grpc_servicer, server)
        server.add_insecure_port(f"[::]:{grpc_port}")
        server.start()
        server.wait_for_termination()


if __name__ == "__main__":
    Server.run()
