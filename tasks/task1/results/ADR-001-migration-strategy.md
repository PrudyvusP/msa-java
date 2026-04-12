# ADR-001: Вынос Booking Service и создание Booking History Service

### **Название задачи:**
Миграция модуля бронирований (Booking) из Java-монолита Hotelio в два отдельных микросервиса на Python: `booking-service` (приём и валидация бронирований) и `booking-history-service` (асинхронная запись событий для аналитики). Первый шаг перехода от монолита к микросервисной архитектуре (паттерн Strangler Fig).

### **Автор:**
Архитектурный анализ

### **Дата:**
2026-04-05

---

### **Функциональные требования**

| № | Действующие лица или системы | Use Case | Описание |
| :-: | :- | :- | :- |
| UC-1 | Клиент (Web/Mobile) | Создание бронирования | Клиент отправляет `POST /api/bookings?userId=...&hotelId=...&promoCode=...`. Booking Service проверяет пользователя (активен, не в чёрном списке), отель (работает, не полностью забронирован, доверенный по отзывам), применяет промокод, рассчитывает цену (VIP — 80, остальные — 100, минус скидка промокода) и сохраняет бронирование в свою БД. |
| UC-2 | Клиент (Web/Mobile) | Просмотр бронирований | Клиент отправляет `GET /api/bookings` или `GET /api/bookings?userId=...`. Booking Service возвращает список бронирований из своей БД. |
| UC-3 | Booking Service | Валидация через монолит | Booking Service вызывает gRPC-методы монолита: `UserService.GetUserInfo`, `HotelService.GetHotelInfo`, `PromoService.ValidatePromo`, `ReviewService.IsHotelTrusted`. |
| UC-4 | Booking Service | Публикация события | После успешного сохранения бронирования Booking Service публикует событие `BookingCreated` в Kafka-топик `bookings`. |
| UC-5 | Booking History Service | Подписка на события | Booking History Service читает события `BookingCreated` из Kafka и сохраняет полную историю бронирований в свою БД для целей аналитики (по пользователям, отелям, дням). |

---

### **Нефункциональные требования**

| № | Требование |
| :-: | :- |
| NFR-1 | Оба сервиса на Python 3.11+, FastAPI |
| NFR-2 | Каждый сервис имеет собственную PostgreSQL базу данных |
| NFR-3 | SQLAlchemy + Alembic для ORM и миграций |
| NFR-4 | gRPC (`grpcio`, `grpcio-tools`) для вызовов Booking Service → монолит |
| NFR-5 | Общие `.proto`-контракты: `user.proto`, `hotel.proto`, `promo.proto`, `review.proto`, `booking.proto` |
| NFR-6 | Kafka (Confluent cp-kafka 7.2.1) + Zookeeper для асинхронной передачи событий |
| NFR-7 | Kafka-producer в booking-service, Kafka-consumer в booking-history-service |
| NFR-8 | Docker-контейнеризация, общая сеть `hotelio-net` |
| NFR-9 | Логирование всех запросов и событий (уровень INFO) |
| NFR-10 | Таймауты и retry-политика на gRPC-вызовы и Kafka |

---

### **Решение**

#### Диаграмма контекста (C4 — Context)

```plantuml
@startuml context
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF

actor "Клиент" as client

component "Booking Service\n[Python, FastAPI]" as booking
component "Java Монолит\n(User, Hotel, Promo, Review)" as monolith
component "Kafka" as kafka
component "Booking History Service\n[Python, FastAPI]" as history

client --> booking : HTTP\nPOST/GET /api/bookings
booking --> monolith : gRPC\nвалидация
booking --> kafka : publish\nBookingCreated
kafka --> history : consume\nBookingCreated

database "PostgreSQL\n(booking_db)" as booking_db
database "PostgreSQL\n(history_db)" as history_db

booking --> booking_db
history --> history_db
@enduml
```

#### Диаграмма контейнеров — Booking Service

```plantuml
@startuml booking_service
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF

component "Booking Service" {

  component "FastAPI Routes\nPOST/GET /api/bookings" as routes

  component "BookingService\n(бизнес-логика)" as logic

  component "gRPC Clients\nUserStub, HotelStub,\nPromoStub, ReviewStub" as grpc_clients

  component "Kafka Producer\n(BookingCreated)" as producer

  component "BookingRepository\n(SQLAlchemy ORM)" as repo

  routes --> logic
  logic --> grpc_clients
  logic --> producer
  logic --> repo

  database "PostgreSQL\n(booking_db)" as db
  repo --> db
}
@enduml
```

#### Диаграмма контейнеров — Booking History Service

```plantuml
@startuml history_service
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF

component "Booking History Service" {

  component "Kafka Consumer\n(BookingCreated)" as consumer

  component "HistoryRepository\n(SQLAlchemy ORM)" as repo

  consumer --> repo

  database "PostgreSQL\n(history_db)" as db
  repo --> db
}
@enduml
```

#### Диаграмма последовательности — Создание бронирования

```plantuml
@startuml sequence_booking
actor "Клиент" as client
participant "Booking Service" as bs
participant "User gRPC" as user
participant "Hotel gRPC" as hotel
participant "Promo gRPC" as promo
participant "Review gRPC" as review
participant "PostgreSQL" as db
participant "Kafka" as kafka

client -> bs : POST /api/bookings?userId&hotelId&promoCode

bs -> user : GetUserInfo(userId)
user --> bs : status, active, blacklisted

bs -> hotel : GetHotelInfo(hotelId)
hotel --> bs : operational, fullyBooked

bs -> review : IsHotelTrusted(hotelId)
review --> bs : trusted

bs -> promo : ValidatePromo(code, userId)
promo --> bs : discountPercent

bs -> bs : calculate final price

bs -> db : save Booking
db --> bs : saved

bs -> kafka : publish BookingCreated

bs --> client : 200 OK (Booking)
@enduml
```

#### Логика принятия решений

1. **Python + FastAPI:** команда не владеет Java. FastAPI — асинхронный фреймворк с автоматической OpenAPI-документацией и минимальным бойлерплейтом.
2. **gRPC для синхронных вызовов:** строгий контракт через `.proto`, бинарный формат, автогенерация клиентов. Монолит уже включает gRPC-зависимости (`grpc-netty`, `grpc-protobuf`, `grpc-stub`).
3. **Kafka для асинхронных событий:** отдел аналитики не имеет доступа к боевой БД. События `BookingCreated` в Kafka позволяют booking-history-service независимо накапливать историю без дополнительной логики в booking-service.
4. **Разделение ответственности:** booking-service занимается валидацией и созданием бронирований. booking-history-service — только чтением из Kafka и записью в свою БД для аналитики.
5. **Database-per-Service:** настоящая независимость. Каждый сервис управляет своей схемой.
6. **Strangler Fig:** постепенная миграция. Монолит работает, booking-service перехватывает `/api/bookings`.

---

### **Альтернативы**

| Альтернатива | Почему отклонена |
| :- | :- |
| **REST вместо gRPC** | gRPC обеспечивает строгий контракт, меньшую задержку. Монолит уже имеет gRPC-зависимости. |
| **Одна БД для обоих сервисов** | Нарушает принцип database-per-service, создаёт coupling. |
| **Добавить аналитику прямо в booking-service** | Нарушает SRP, увеличивает нагрузку на критичный сервис. |
| **Big Bang миграция** | Слишком рискованно. Strangler Fig позволяет откатиться. |
| **HTTP polling вместо Kafka** | Неэффективно, задержки, лишняя нагрузка. |

#### Недостатки, ограничения, риски

| Риск | Влияние | Митигация |
| :- | :- | :- |
| `ddl-auto: create` в монолите стирает данные при каждом рестарте | 🔴 Высокая | Первым делом заменить на `validate` или `update` |
| gRPC-сервер нужно поднять в монолите (сейчас только REST) | 🔴 Высокая | Добавить `.proto` файлы и gRPC-эндпоинты в монолит как подготовительный шаг |
| Синхронные gRPC-вызовы — цепочка из 4 зависимостей на каждый запрос | Средняя | Таймауты, circuit breaker. В будущем — кэширование. |
| Kafka-события могут потеряться при недоступности consumer | Средняя | Kafka гарантирует persistence, retry в consumer. Idempotency-ключи. |
| Две разные кодовые базы (Java + Python) усложняют поддержку | Средняя | Общие `.proto` как единый источник правды. |
| Промокод и цена — хардкод (VIP=80, остальные=100) | Низкая | Копируем как есть, рефакторинг — отдельная задача. |

---

### **План миграции (Strangler Fig)**

| Фаза | Задачи | Результат |
| :- | :- | :- |
| **0. Подготовка** | Исправить `ddl-auto`. Определить `.proto` контракты (`booking.proto`, `user.proto`, `hotel.proto`, `promo.proto`, `review.proto`). Реализовать gRPC-эндпоинты в монолите. | Монолит стабилен, gRPC готов |
| **1. Booking Service — скелет** | Python/FastAPI проект, gRPC-клиенты из `.proto`, Docker, `GET /api/bookings` через gRPC к монолиту. Собственная БД (SQLAlchemy + Alembic). | Сервис запускается, читает данные |
| **2. Booking Service — полная логика** | `POST /api/bookings` с валидациями через gRPC и расчётом цен. Kafka-producer публикует `BookingCreated`. | Полная parity с монолитом |
| **3. Booking History Service** | Kafka-consumer читает `BookingCreated`, сохраняет в свою БД. Эндпоинты для аналитики (по пользователям, отелям, дням). | Аналитика работает |
| **4. Роутинг** | API Gateway: `/api/bookings/**` → booking-service. Canary 10%. Environment: `BOOKING_SERVICE_EXTERNAL_HOST`, `BOOKING_SERVICE_EXTERNAL_PORT`. | Трафик перенаправлен |
| **5. Отрезание** | Удалить Booking-код из монолита. Миграция данных. Убедиться, что booking-history-service продолжает получать события. | Оба сервиса независимы |
