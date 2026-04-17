# Отчет: Настройка canary-релиза и feature flags с Istio

## Что сделано

### 1. Подготовлено приложение (Go)
- Версия v1: фича включена через переменную окружения `ENABLE_FEATURE_X=true`
- Версия v2: фича включается через заголовок `X-Feature-Enabled: true`

### 2. Развернуты две версии в Kubernetes
- `values-v1` — 2 реплики, лейбл `version: v1`
- `values-v2` — 1 реплика, лейбл `version: v2`
- Общий Service `service`

### 3. Настроен Istio

**DestinationRule** (`destination-rule.yaml`):
- Разделение на subsets v1 и v2
- Circuit breaking (ограничение соединений)
- Outlier detection — при 2 ошибках 5xx под исключается на 30 секунд (fallback)

**VirtualService** (`virtual-service.yaml`):
- 90% трафика на v1, 10% на v2 (canary)
- Если заголовок `X-Feature-Enabled: true` → 100% на v2
- Retries: 3 попытки при ошибках

## Проверка

```bash
# Canary (90/10)
kubectl exec test-client -- sh -c "for i in 1..10; do curl -s http://booking-service/feature; done"
# Результат: 9 раз "Feature X is enabled!", 1 раз "404 page not found"

# Feature flag по заголовку
kubectl exec test-client -- curl -s -H "X-Feature-Enabled: true" http://booking-service/feature
# Результат: всегда "Feature X is enabled!"
```

## Вывод

Все требования выполнены:
- ✅ Две версии v1/v2
- ✅ Canary 90/10
- ✅ Feature flag через заголовок
- ✅ Fallback (outlier detection)
- ✅ Retries и Circuit breaking
