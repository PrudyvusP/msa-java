import time

from .db import Booking
from .generated import booking_pb2, booking_pb2_grpc
from .interfaces.booking_producer import IBookingEventProducer


class BookingServiceServicer(booking_pb2_grpc.BookingServiceServicer):
    def __init__(self, booking_producer: IBookingEventProducer, session_factory):
        self._booking_producer = booking_producer
        self._session_factory = session_factory

    def CreateBooking(self, request, context):
        user_id = request.user_id
        hotel_id = request.hotel_id
        promo_code = request.promo_code if request.promo_code else None

        # TODO: gRPC-вызовы к монолиту для валидации (user, hotel, promo, review)
        # Пока заглушки — рассчитываем цену как в монолите

        discount_percent = 0.0
        if promo_code:
            # TODO: вызвать PromoService.ValidatePromo через gRPC
            discount_percent = 10.0  # заглушка

        base_price = 80.0  # TODO: зависит от статуса пользователя (VIP=80, иначе=100)
        final_price = base_price - discount_percent

        booking_id = str(int(time.time() * 1000))

        booking = Booking(
            id=booking_id,
            user_id=user_id,
            hotel_id=hotel_id,
            promo_code=promo_code,
            discount_percent=discount_percent,
            price=final_price,
        )

        with self._session_factory() as session:
            session.add(booking)
            session.commit()
            session.refresh(booking)

        self._booking_producer.publish(
            {
                "id": booking_id,
                "user_id": user_id,
                "hotel_id": hotel_id,
                "promo_code": promo_code,
                "discount_percent": discount_percent,
                "price": final_price,
            }
        )

        return booking_pb2.BookingResponse(
            id=booking_id,
            user_id=user_id,
            hotel_id=hotel_id,
            promo_code=promo_code or "",
            discount_percent=discount_percent,
            price=final_price,
            created_at=booking.created_at.isoformat(),
        )

    def ListBookings(self, request, context):
        user_id = request.user_id if request.user_id else None

        with self._session_factory() as session:
            query = session.query(Booking)
            if user_id:
                query = query.filter(Booking.user_id == user_id)
            bookings = query.all()

        return booking_pb2.BookingListResponse(
            bookings=[
                booking_pb2.BookingResponse(
                    id=b.id,
                    user_id=b.user_id,
                    hotel_id=b.hotel_id,
                    promo_code=b.promo_code or "",
                    discount_percent=b.discount_percent or 0.0,
                    price=b.price,
                    created_at=b.created_at.isoformat(),
                )
                for b in bookings
            ]
        )
