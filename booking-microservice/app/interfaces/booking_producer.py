from abc import ABC, abstractmethod


class IBookingEventProducer(ABC):
    @abstractmethod
    def publish(self, booking: dict) -> None:
        """Опубликовать событие о бронировании."""
