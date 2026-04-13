FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY main.go .
RUN go build -o booking-service main.go

FROM alpine:3.19

RUN apk add --no-cache curl

WORKDIR /app
COPY --from=builder /app/booking-service .

EXPOSE 8080
CMD ["./booking-service"]
