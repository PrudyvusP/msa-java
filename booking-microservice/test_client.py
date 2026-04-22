"""Полностью сгенерировано QWEN-CODER !!!!

Тестовый клиент для booking-service.
Проверяет:
  1. CreateBooking через gRPC
  2. ListBookings через gRPC
  3. Событие в Kafka
  4. Запись в PostgreSQL
"""

import json
import sys

import grpc
from app.generated import booking_pb2, booking_pb2_grpc
from confluent_kafka import Consumer

GRPC_TARGET = "localhost:9090"
KAFKA_BROKER = "localhost:9093"
KAFKA_TOPIC = "booking-events"
DB_HOST = "localhost"
DB_PORT = 54321
DB_NAME = "booking"
DB_USER = "booking"
DB_PASS = "booking"


def test_create_booking():
    """1. Создаём бронирование через gRPC."""
    print("=" * 60)
    print("1. CreateBooking (gRPC)")
    print("=" * 60)

    with grpc.insecure_channel(GRPC_TARGET) as channel:
        stub = booking_pb2_grpc.BookingServiceStub(channel)

        response = stub.CreateBooking(
            booking_pb2.BookingRequest(
                user_id="test-user-2",
                hotel_id="test-hotel-1",
                promo_code="TESTCODE1",
            )
        )

        print(f"  ✅ id:               {response.id}")
        print(f"  ✅ user_id:          {response.user_id}")
        print(f"  ✅ hotel_id:         {response.hotel_id}")
        print(f"  ✅ promo_code:       {response.promo_code}")
        print(f"  ✅ discount_percent: {response.discount_percent}")
        print(f"  ✅ price:            {response.price}")
        print(f"  ✅ created_at:       {response.created_at}")

        return response.id


def test_list_bookings():
    """2. Получаем все бронирования через gRPC."""
    print("\n" + "=" * 60)
    print("2. ListBookings (gRPC)")
    print("=" * 60)

    with grpc.insecure_channel(GRPC_TARGET) as channel:
        stub = booking_pb2_grpc.BookingServiceStub(channel)

        response = stub.ListBookings(booking_pb2.BookingListRequest(user_id=""))
        print(f"  Всего записей: {len(response.bookings)}")
        for b in response.bookings:
            print(f"  [{b.id}] {b.user_id} → {b.hotel_id}  price={b.price}")

        return len(response.bookings)


def test_kafka_event():
    """3. Проверяем, что событие попало в Kafka."""
    print("\n" + "=" * 60)
    print("3. Kafka — проверка события")
    print("=" * 60)

    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": "test-consumer",
            "auto.offset.reset": "earliest",
            "session.timeout.ms": 10000,
        }
    )
    consumer.subscribe([KAFKA_TOPIC])

    # Ждём сообщение до 10 секунд
    for _ in range(20):
        msg = consumer.poll(timeout=0.5)
        if msg and msg.value():
            event = json.loads(msg.value().decode("utf-8"))
            print(f"  ✅ Топик: {msg.topic()}")
            print(f"  ✅ Partition: {msg.partition()}, Offset: {msg.offset()}")
            print(f"  ✅ Event type: {event.get('type_')}")
            payload = event.get("payload", {})
            print(f"  ✅ Payload user_id: {payload.get('user_id')}")
            print(f"  ✅ Payload hotel_id: {payload.get('hotel_id')}")
            print(f"  ✅ Payload price: {payload.get('price')}")
            consumer.close()
            return True

    consumer.close()
    print("  ❌ Событие не найдено в Kafka (таймаут)")
    return False


def test_db_record():
    """4. Проверяем запись в PostgreSQL."""
    print("\n" + "=" * 60)
    print("4. PostgreSQL — проверка записей")
    print("=" * 60)

    try:
        import psycopg2
    except ImportError:
        print("  ⚠️  psycopg2 не установлен. Установите: pip install psycopg2-binary")
        print("  🔄 Проверка через psql:")
        print(f"     psql -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME}")
        print("     SELECT * FROM bookings;")
        return False

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, hotel_id, price, promo_code, created_at FROM bookings ORDER BY created_at"
    )
    rows = cur.fetchall()

    print(f"  Всего записей: {len(rows)}")
    for row in rows:
        print(f"  [{row[0]}] {row[1]} → {row[2]}  price={row[3]}  promo={row[4]}")

    cur.close()
    conn.close()
    return len(rows)


def main():
    print("🧪 Тестирование booking-microservice")
    print()

    booking_id = test_create_booking()
    count = test_list_bookings()
    kafka_ok = test_kafka_event()
    db_count = test_db_record()

    print("\n" + "=" * 60)
    print("📊 Итого")
    print("=" * 60)
    print("  gRPC CreateBooking:  ✅")
    print(f"  gRPC ListBookings:   ✅ ({count} записей)")
    print(f"  Kafka event:         {'✅' if kafka_ok else '❌'}")
    print(
        f"  DB records:          {db_count if isinstance(db_count, int) else '⚠️ не проверено'}"
    )
    print()

    if kafka_ok and isinstance(db_count, int) and db_count > 0:
        print("🎉 Все проверки пройдены!")
        sys.exit(0)
    else:
        print("⚠️  Не все проверки пройдены — см. вывод выше")
        sys.exit(1)


if __name__ == "__main__":
    main()

