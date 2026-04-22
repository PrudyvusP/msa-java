-- Начальные данные для booking-db (аналогично монолиту)
INSERT INTO bookings (id, user_id, hotel_id, promo_code, discount_percent, price, created_at)
VALUES
  ('init-booking-1', 'test-user-2', 'test-hotel-1', 'TESTCODE1', 10.0, 90.0, NOW()),
  ('init-booking-2', 'test-user-3', 'test-hotel-1', NULL, 0.0, 80.0, NOW())
ON CONFLICT (id) DO NOTHING;
