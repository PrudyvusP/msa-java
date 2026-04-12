# Отчёт: GraphQL Federation — Личный кабинет

## Внесённые изменения

### 1. booking-subgraph (`booking-subgraph/index.js`)

**Что реализовано:**

- **ACL на уровне resolver'а** — `bookingsByUser` проверяет заголовок `userid`. Если заголовок отсутствует — возвращается ошибка `Unauthorized`. Если `userid` не совпадает с запрашиваемым `userId` — возвращается ошибка `Forbidden`. Пользователь видит только свои бронирования.
- **Ссылка на Hotel** — в тип `Booking` добавлено поле `hotel: Hotel`. Resolver возвращает ссылку `{ __typename: 'Hotel', id: booking.hotelId }`, которую Apollo Federation автоматически разрешает через hotel-subgraph.
- **`extend type Hotel`** — объявлена внешняя сущность из hotel-subgraph с `@external` директивой.
- **Заглушка данных** — массив `bookings` с тремя записями для двух пользователей. В комментарии указано место для замены на gRPC-вызов к booking-service из задания 2.

### 2. hotel-subgraph (`hotel-subgraph/index.js`)

**Что реализовано:**

- **`__resolveReference`** — разрешает ссылку на Hotel по `id`. Вызывается автоматически, когда Apollo Federation получает `{ __typename: 'Hotel', id: ... }` из booking-subgraph.
- **`hotelsByIds`** — query для получения отелей по списку ID.
- **Заглушка данных** — массив `hotels` с тремя отелями. В комментарии указано место для замены на REST/gRPC-вызов к hotel-сервису.

### 3. apollo-gateway (`gateway/index.js`)

**Что реализовано:**

- **`AuthenticatedDataSource`** — кастомный `RemoteGraphQLDataSource` с хуком `willSendRequest`, который пробрасывает заголовок `userid` из входящего запроса во все подграфы. Без этого ACL в booking-subgraph не получил бы информацию об аутентифицированном пользователе.
- **`buildService`** — фабрика, которая создаёт `AuthenticatedDataSource` для каждого подграфа вместо стандартного `RemoteGraphQLDataSource`.
