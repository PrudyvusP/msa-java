# Отчёт — Задание 4: Автоматизация развёртывания и тестирования

## Описание изменений

### 1. Docker-образ booking-service
- **Dockerfile** на основе `golang:1.21-alpine` (multi-stage build)
- Порт 8080, endpoint `/ping` возвращает `pong`
- При `ENABLE_FEATURE_X=true` поведение сервиса меняется (feature flag)
- Собирается через `docker build -t booking-service:latest ./booking-service/`

### 2. Helm-чарт
- **Deployment** с `livenessProbe` и `readinessProbe` по `/ping`
- **Service** типа ClusterIP (port 80 → targetPort 8080)
- Настраивается через `values.yaml`: replicaCount, image, env, resources
- Два варианта конфигурации:
  - `values-staging.yaml` — 1 реплика, минимальные ресурсы, `pullPolicy: Never`
  - `values-prod.yaml` — 2 реплики, увеличенные ресурсы, `pullPolicy: IfNotPresent`

### 3. CI/CD-пайплайн (.gitlab-ci.yml)
- **build**: `docker build`
- **test**: запуск контейнера, проверка `/ping`, очистка
- **deploy**: `minikube image load` + `helm upgrade --install`
- **tag**: создание git-тега с timestamp

Запуск локально: `gitlab-ci-local build test deploy tag`

### 4. Service Discovery через DNS
- DNS-имя `booking-service` резолвится внутри кластера Minikube
- Проверка: `./check-dns.sh` — запускает busybox-под с `wget http://booking-service/ping`

## Ключевые решения

- **imagePullPolicy: Never** — для использования локального образа без registry
- **minikube image load** — загрузка образа в Minikube без Docker Registry
- Прокси: при использовании прокси необходимо добавить `192.168.49.0/24` в `NO_PROXY`

## Инструкция по разворачиванию

```bash
# 1. Запуск Minikube
minikube start --driver=docker

# 2. (При наличии прокси) Добавить в NO_PROXY
export NO_PROXY=localhost,127.0.0.0/8,::1,192.168.49.0/24

# 3. Загрузка образа
minikube image load booking-service:latest

# 4. Установка через Helm
helm upgrade --install booking-service ./helm/booking-service/ \
  --set image.name=booking-service \
  --set image.tag=latest \
  --set image.pullPolicy=Never

# 5. Проверка
kubectl port-forward svc/booking-service 8080:80 &
curl http://localhost:8080/ping

# 6. DNS тест
./check-dns.sh

# 7. Статус
./check-status.sh
```