# Microservices OTEL Demo

This project contains two Spring Boot microservices using **Micrometer** with an **OpenTelemetry** backend and a **Zipkin** exporter:

- `account-service` – exposes a list of bank accounts on `GET /accounts`
- `client-service` – calls `account-service` and exposes `GET /client/accounts`

Both services:
- Use Micrometer metrics (`MeterRegistry`) and timers/counters
- Use Micrometer Tracing with the OpenTelemetry bridge
- Export spans to Zipkin (via the OpenTelemetry Zipkin exporter)
- Log `traceId` and `spanId` in each log line for correlation

## Prerequisites

- JDK 17+
- Maven 3.9+
- Docker (for running Zipkin easily)

## Start Zipkin

```bash
docker run -d -p 9411:9411 openzipkin/zipkin
```

Zipkin UI: http://localhost:9411

## Build and Run

From the project root (`microservices-otel-demo`):

```bash
mvn clean package
```

### Run account-service

```bash
cd account-service
mvn spring-boot:run
```

This starts on port **8081**.

Test:

```bash
curl http://localhost:8081/accounts
```

### Run client-service

In a new terminal:

```bash
cd client-service
mvn spring-boot:run
```

This starts on port **8082**.

Test:

```bash
curl http://localhost:8082/client/accounts
```

You should see the list of bank accounts returned, and a distributed trace flowing from:

1. `client-service` HTTP server span  
2. `client-service` WebClient client span  
3. `account-service` HTTP server span  

All visible in Zipkin with the same `traceId`.

## Notes

- Tracing is enabled via `micrometer-tracing-bridge-otel` and the `opentelemetry-exporter-zipkin` dependency.
- The exporter beans are configured via `OpenTelemetryZipkinConfig` in each service.
- Logging patterns in `application.yml` include `traceId` and `spanId`.

